# 复习笔记：DocumentSplitNode（document_split_node）

> 文件：`nodes/document_split_node.py`  
> 定位：导入流水线中，把处理后的 MD 切成可向量化的 `chunks`（保结构 + 控长度）。

---

## 1. 节点在图谱中的位置

```text
… → md_to_img_node → document_split_node → item_name_recognition_node → embedding → milvus
```

- 输入：`state['md_content']`、`file_title`、`file_dir`  
- 输出：`state['chunks']`，并备份 `chunks.json`  

---

## 2. 为什么要切分（RAG 动机）

| 问题 | 做法 |
|------|------|
| 整篇进向量库太粗，检索不准 | 切成语义完整的小块 |
| 乱切会切断标题结构 | **先按标题切**（一级策略） |
| 单章太长 / 太碎 | **再切长、合短**（二级策略） |

一句话：**标题保结构，阈值控长度。**

---

## 3. 整体流程（process）

```text
1. _validate_state      校验参数、统一换行符
2. _split_by_headings   按 #～###### 切成 sections
3. _split_and_merge     先切长 section，再合短 section
4. _assemble_chuks      组装成 chunk（content = title + \n\n + body）
5. _backup              写 chunks.json
6. state['chunks'] = …
```

默认配置（`config.py`）：

| 参数 | 默认 | 含义 |
|------|------|------|
| `max_content_length` | 1000 | 单块最大长度（按 title+\n\n+body 计） |
| `min_content_length` | 500 | 短于该值且同源则尝试合并 |

要求：`max > min > 0`。

---

## 4. Section 数据结构

一级切分后的章节对象：

```python
{
  "body": "正文",
  "title": "当前标题（无标题时用 file_title）",
  "parent_title": "父级标题（短片合并用）",
  "file_title": "文档名"
}
```

最终 chunk：

```python
{
  "content": f"{title}\n\n{body}",  # 真正进 embedding 的文本
  "title": ...,
  "parent_title": ...,
  "file_title": ...
}
```

---

## 5. `_split_by_headings` — 一级：按标题切

### 5.1 目标

遇到 Markdown 标题就封上上一章，把「标题之间的内容」打成多个 section。

### 5.2 核心状态

| 变量 | 作用 |
|------|------|
| `in_fence` | 是否在 `` ``` `` / `~~~` 代码块内 |
| `body_lines` | 当前章正在收集的正文行 |
| `current_title` / `current_level` | 当前标题及级别 1～6 |
| `hierarchy[1..6]` | 各级标题面包屑，用来找父标题 |
| `sections` | 输出列表 |

### 5.3 逐行逻辑

```text
对每一行：
  1. 若是代码围栏 → 翻转 in_fence
  2. 不在代码块，且匹配 ^(#{1,6})\s+(.+)$ → 真标题
       - _flush() 打包上一章
       - 更新 current_title / level / hierarchy[level]
       - 清空 level 以下的 hierarchy（防旧下级残留）
       - body_lines = []
  3. 否则 → body_lines.append(行)
扫完再 _flush() 一次
```

**代码块内的 `#` 不当标题**，避免把注释切成章节。

### 5.4 `_flush()` 打包规则

- `title` 或 `body` 有一个非空 → 打包  
- 两者都空 → 不打包  

### 5.5 找父标题（重点）

```python
for i in range(current_level - 1, 0, -1):
    if hierarchy[i]:
        parent_title = hierarchy[i]
        break
```

从「上一级」往 1 级倒着找，**第一个非空**就是最近祖先；空槽跳过。

例：当前是 `### 环境要求`（level=3）

```text
hierarchy[1] = "# 产品手册"
hierarchy[2] = "## 安装说明"
hierarchy[3] = "### 环境要求"

i=2 → "## 安装说明" → parent_title（break）
```

若 `hierarchy[2]` 为空，会继续到 `i=1` 用 `# 产品手册`。

一级标题时 `range(0,0,-1)` 空循环，兜底：

```python
parent_title = current_title or file_title
```

遇到新的同级/上级标题时清空下级：

```python
hierarchy[level] = current_title
for i in range(level + 1, 7):
    hierarchy[i] = ""
```

---

## 6. `_split_and_merge` — 二级：先切后合

```text
对每个 section → _split_long_section（超长则切）
全部切完后   → _merge_short_section（过短且同源则合）
```

顺序固定：**先切后合**，避免先合出超长块再难切。

---

## 7. `_split_long_section` — 切太长的章

### 7.1 预处理

- `title` 超过 80 字符则截断（防御）  
- body 含 `<table>` → `MarkdownTableLinearizer` 表格线性化，方便按文本切  

### 7.2 `title_prefix`（重点）

```python
title_prefix = f"{title}\n\n"
total_length = len(title_prefix) + len(body)
body_length = max_content_length - len(title_prefix)
```

最终 content 形态是 `标题 + 空行 + 正文`，长度必须按这个算。  
只算 `len(title)+len(body)` 会少算两个 `\n`，可能切完再拼又超限。

### 7.3 递归字符切分器

未超长 → 原 section 原样返回。  
超长 → 用 LangChain `RecursiveCharacterTextSplitter` **只切 body**：

| 参数 | 取值 | 含义 |
|------|------|------|
| `chunk_size` | `body_length` | 每段 body 上限 |
| `chunk_overlap` | 0 | 不重叠 |
| `separators` | `\n\n` → `\n` → 中英文标点 → 空格 → `""` | 尽量在自然边界切 |
| `keep_separator` | True | 保留分隔符 |

切完后子 section：

```python
{
  "body": 子段,
  "title": f"{title}_{index+1}",  # 如 ## 安装_1
  "parent_title": 原 parent_title,  # 同源合并仍认原来的父
  "file_title": ...
}
```

---

## 8. `_merge_short_section` — 合太短的章

### 8.1 短章节来源

1. 一级按标题切完本身就很短  
2. 二次递归切分产生的尾巴很短  

### 8.2 合并条件（同时满足）

1. 当前 `body` 长度 `< min_content_length`  
2. **同源**：`parent_title` 相同  

父标题不同即使很短也不合，避免跨章粘连。

### 8.3 滑动指针逻辑

```text
current = sections[0]
对 next in sections[1:]:
  能合 → current.body += "\n\n" + next.body
         current.title = parent_title   # 标题回退为父标题
  不能 → final.append(current); current = next
最后 final.append(current)
```

- `rstrip` / `lstrip`：拼接时去掉多余空白  
- 合完后若仍短且下一段仍同源，可继续合（一进一出式往后粘）  
- 注解里写成 `Dict` 是笔误，实际是 **`List[Dict]`**

---

## 9. `_assemble_chuks` / `_backup`

- 组装：`content = f"{title}\n\n{body}"`，带上元数据字段  
- 备份：`{file_dir}/chunks.json`，方便肉眼检查切分效果  
- 方法名拼写：`_assemble_chuks`（缺了 n），属历史命名  

---

## 10. 端到端小例子

```markdown
# 产品手册
概述文字。

## 安装
很短。

## 使用
很长很长……（超过 max）
```

大致过程：

1. 标题切 → 3 个 section（概述 / 安装 / 使用）  
2. 「使用」超长 → 切成 `使用_1`、`使用_2`…，`parent_title` 仍指向上级  
3. 「安装」过短且与下一段若同源才合；否则保持独立  
4. 每段拼成 `title\n\nbody` 进入 `chunks`  

---

## 11. 面试速记

**Q：为什么不直接 Recursive 切全文？**  
先按标题切能保留章节语义；纯字符切容易把「安装」和「故障」粘/切断。

**Q：parent_title 干什么？**  
短 chunk 合并时的同源判据；只合同一父标题下的碎段。

**Q：title_prefix 为什么带 `\n\n`？**  
与最终 `content` 排版一致，长度计算才准。

**Q：先切后合还是先合后切？**  
本实现先切后合：先保证不超 max，再收拾碎段。

**Q：代码块怎么处理？**  
`in_fence` 翻转；围栏内不识别标题。

---

## 12. 易错 / 代码现状注意

1. `_split_long_section` 里 `if len(sections)==1: return [sections]` 返回的是**字符串列表套一层**，类型可能和 section dict 不一致（潜在 bug）  
2. `_merge_short_section` 空列表会直接 `current_sections[0]` 报错（无 section 边界）  
3. 合并只看「当前是否短」，不强制合并后仍 ≤ max（通常二次切后问题不大，极端情况可超）  
4. 方法名 `_assemble_chuks`、类型注解 `Dict` vs `List` 面试时可主动提到  

---

## 13. 一句话收束

**按标题拆章并记下父子关系 → 超长用递归分隔符切 body → 过短且同源则粘合 → 拼成 title\\n\\nbody 的 chunks 交给下游商品名识别与向量化。**
