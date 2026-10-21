# 复习笔记：MarkDownToImgNode（md_to_img_node）

> 文件：`nodes/md_to_img_node.py`  
> 定位：导入流水线中，把 MD 里的图片「降维」成可检索文本，原图进对象存储。

---

## 1. 节点在图谱中的位置

```text
entry_node
  ├─ pdf → pdf_to_md_node ─┐
  └─ md  ──────────────────┴→ md_to_img_node → document_split_node → …
```

- 上游：PDF 经 MinerU 产出 MD + `images/`，或直接上传 MD  
- 本节点：图 → 文摘要 + 上传 MinIO + 回写 MD  
- 下游：切分 / 商品名 / embedding 都吃**文本**，吃不到纯像素，所以必须做这一步  

---

## 2. 为什么要这个节点（业务动机）

| 问题 | 做法 |
|------|------|
| 文本 embedding 看不懂图 | 用 **VLM** 生成中文摘要标题，嵌入 MD |
| 原图还要展示 / 溯源 | 上传 **MinIO**，MD 里换成远程 URL |
| 摘要要贴合文档语义 | 抽取图片上下文章节，一起喂给 VLM |

一句话：**多模态 RAG 的「图转文」降维节点。**

---

## 3. 整体流程（process 五步）

```text
step1  _MdFileHandler     读 MD、定 images 目录
step2  _ImageScanner      扫图 + 抽上下文 → List[ImageInfo]
step3  _VLMSummarizer     VLM 生成摘要 → {文件名: 摘要}
step4  _ImageUploader     上传 MinIO + 替换 MD 中 ![alt](url)
step5  _MdFileHandler     备份为 xxx_new.md，写入 state['md_content']
```

节点类本身**只编排**，业务细节在四个协作类里。

---

## 4. 数据结构

### ImageContext
一张图在 MD 里的语境：

| 字段 | 含义 |
|------|------|
| `head` | 最近上文标题（`#`～`######`） |
| `pre_text` | 上文正文（限长、按段落截） |
| `post_text` | 下文正文（限长；不要下文标题） |

### ImageInfo
一张图的完整信息：

| 字段 | 用途 |
|------|------|
| `name` | 文件名，作摘要 / URL 字典的 key |
| `path` | 本地路径：读字节给 VLM、上传 MinIO |
| `image_context` | 给 VLM 的文本背景 |

---

## 5. 四个协作类（不是继承，是组合）

> 问：能不能合成一个类？**能**，功能等价。  
> 拆开为了：单一职责、好测、好换模型/存储、和 step 对齐。

### 5.1 `_MdFileHandler` — 读 / 备份

**读：**
1. 从 state 取 `md_path`，校验存在  
2. 读出 `md_content`  
3. 图片目录约定：`md 同级 / images`

**备份：**

```python
new_file_path = md_path_obj.with_name(
    f"{md_path_obj.stem}_new{md_path_obj.suffix}"
)
```

- `.stem`：无后缀名；`.suffix`：含点的后缀  
- `.with_name(...)`：同目录，只换文件名  
- 例：`万用表的使用.md` → `万用表的使用_new.md`  
- 不覆盖原文件，方便对比测试  

```python
with open(new_file_path, "w", encoding="utf-8") as f:
    f.write(new_md_content)
```

- 内容已在内存里，一次 `write` 对常规手册 MD（KB～数 MB）没问题  
- 瓶颈是内存/磁盘，不是 `write` API 本身  

### 5.2 `_ImageScanner` — 扫目录 + 抽上下文

**入口思路：**

```python
img_info_list = []
for img_path in img_dir_obj.iterdir():
    ...
```

#### `iterdir()` 精讲

- `img_dir_obj` 是 `pathlib.Path`（`images/`）  
- `.iterdir()`：**只遍历当前这一层**，每次产出一个子路径 `Path`  
- 文件和子目录都会出现 → 后面要用 `is_file()` 过滤  
- **不保证顺序**；目录为空则循环不执行，返回 `[]`  

比 `os.listdir` 方便：直接得到 Path，可写 `.suffix` / `.name`。

#### 过滤与组装

对每个 `img_path`：
1. 非文件 → skip  
2. 后缀不在 `config.image_extensions` → skip  
3. 用文件名在 MD 里找引用，抽上下文；找不到 → skip  
4. 封装 `ImageInfo`，`append` 到列表  

**为何以目录为准扫，而不是只解析 MD？**  
磁盘路径用于读图、上传；MD 负责定位引用和上下文。两边对齐才有效。

#### 上下文策略（面试重点）

**上文：**
1. 从图片行往上找到最近标题  
2. 标题与图片之间的行作上文  
3. **按段落**截断到 `img_content_length`（默认 200），避免硬切字破坏语义  
4. 就近原则：从靠近图片的段落往外凑  

**下文：**
1. 从图片行往下找到最近标题（作边界，**不要标题内容**）  
2. 同样按段落限长  

**为何上下文都要？**  
图可能在段前 / 段后 / 段中，只留一侧信息不完整。  
其他图片行当作段落边界丢掉，避免串图语义。

正则抓图引用示例：

```text
![img2](images/万用表的使用_img2.jpg)
pattern ≈ !\[.*?\]\(.*?{img_name}.*?\)
```

### 5.3 `_VLMSummarizer` — 视觉语言模型摘要

#### VLM 是什么

- **VLM** = Vision-Language Model（视觉语言模型）  
- 属于**多模态大模型**的一类：同时处理视觉 + 语言  
- 关系：`多模态 ⊃ VLM（图+文）`  

本项目配置：`VL_MODEL=qwen3-vl-flash`（通义 **Qwen3-VL-Flash**）。

#### 和 MinerU 里「VLM」的区别

| | md_to_img 的 VLM | MinerU 的 VLM |
|--|------------------|---------------|
| 模型 | Qwen3-VL-Flash（API） | 如 MinerU2.5 本地/引擎 |
| 干什么 | **已有图 → 中文摘要** | **PDF 页 → Markdown 结构** |

#### `_summary_all` / `_summary_one`

1. 取 VLM 客户端；失败则全部填「暂无摘要」兜底  
2. 对每张图：限流 → `_summary_one`  
3. 拼上下文：`head + pre_text + post_text`  
4. 本地文件读字节 → Base64 → `image_url` 发给模型  
5. Prompt：结合文档名 + 上下文，生成**短中文标题摘要**（不要带「图片」二字）  
6. 异常返回「暂无图片描述」  

#### `_enforce_rate_limit`（滑动窗口限流）

**设计意图：** 控制每分钟调用次数，避免打爆 API。

调用点：每张图摘要前。

**完整实现思路（当前代码里可能是 `pass` 空实现，属常见坑）：**

```python
def _enforce_rate_limit(self, timestamps: Deque[float], max_requests: int, window: int = 60):
    now = time.time()
    # 1) 丢掉窗口外的旧时间戳
    while timestamps and now - timestamps[0] >= window:
        timestamps.popleft()

    # 2) 窗口内已满 → 睡到最旧那次刚好过期
    if len(timestamps) >= max_requests:
        sleep_dur = window - (now - timestamps[0])
        if sleep_dur > 0:
            time.sleep(sleep_dur)
        now = time.time()
        while timestamps and now - timestamps[0] >= window:
            timestamps.popleft()

    # 3) 登记本次请求时间
    timestamps.append(now)
```

- `timestamps`：队头最旧、队尾最新  
- `max_requests`：对应 `requests_per_minute`（配置默认 15）  
- `window`：默认 60 秒  

一句话：**过去一分钟满了就等到最早一次滑出窗口，再记账放行。**

### 5.4 `_ImageUploader` — 上传 + 改写 MD

1. `_upload_all`：MinIO `fput_object`；失败用本地 path 兜底  
2. 远程 URL 形如：`{minio_base}/{bucket}/{文档stem}/{图片名}`  
3. `_update_md`：正则 `!\[(.*?)\]\((.*?)\)`，按文件名匹配后换成  

```text
![VLM摘要](远程URL)
```

这样切分与 embedding 吃到的是**摘要文本**，展示仍可点开远程图。

---

## 6. 配置相关（import config）

| 配置 | 作用 |
|------|------|
| `img_content_length` | 上下文最大字符（默认 200） |
| `image_extensions` | 允许的图片后缀 |
| `vl_model` | 环境变量 `VL_MODEL` |
| `requests_per_minute` | VLM RPM（默认 15） |
| MinIO 相关 | endpoint / bucket / secure → base URL |

---

## 7. 写入 state 的结果

- `state['md_content']` = 替换摘要与 URL 后的新 MD  
- 磁盘备份：`{stem}_new.md`  
- 原 `md_path` 一般仍指向原文件（备份是另存）  

---

## 8. 设计问答（面试速记）

**Q：为什么拆四个类？**  
组合按职责拆：IO、上下文、多模态、存储。节点只编排。可合成一个，拆开为了测和维护。

**Q：为什么用 VLM？**  
纯文本向量模型看不懂图；摘要进文本链路后才能检索到「图里说了什么」。

**Q：iterdir 为什么这么写？**  
按 `images/` 真实文件枚举；再回 MD 找引用。Path API 干净，一层目录足够。

**Q：限流怎么做？**  
滑动窗口 + deque；满则 sleep。注意代码若是 `pass` 要承认「设计了但未落地」。

**Q：和 PdfToMd / MinerU 的关系？**  
MinerU（或纯 MD）先出图和 MD；本节点做图转文与对象存储，二者不是同一个「VLM」。

---

## 9. 易错 / 代码现状注意

1. `if not img_dir_obj`：Path 对象几乎恒为真，**不能**用来判断目录是否存在，应 `img_dir_obj.exists()`  
2. `_enforce_rate_limit` 若为 `pass`，等于无限流  
3. `_update_md` 的 `replacer` 未匹配时可能隐式返回 `None`，极端情况要注意  
4. 大量图片时：限流 + 失败兜底（暂无摘要 / 本地路径）是稳定性关键  

---

## 10. 一句话收束

**读 MD → 扫 images 并抽章节上下文 → Qwen3-VL 写摘要 → 原图进 MinIO → MD 换成「摘要+远程链」→ 备份 `_new.md`，交给后续文本切分与向量化。**
