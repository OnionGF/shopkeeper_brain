# 今日复习：EntryNode + PdfToMdNode

> 结合代码现状整理（含今日澄清：MinerU 解析方式 / 子进程 / 线程）

---

## 1. EntryNode（入口路由）

### 职责
根据上传文件后缀，给后续条件边写「路标」，并补齐标题。

### 核心逻辑
1. 校验 `import_file_path`、`file_dir` 非空且路径存在  
2. 按后缀分支：
   - `.pdf` → `is_pdf_read_enabled=True`，写 `pdf_path`
   - `.md` → `is_md_read_enabled=True`，写 `md_path`
   - 其他 → `ValidationError`
3. `file_title = Path.stem`（无后缀文件名）

### 和图谱的关系
```
entry_node
    │ 条件边 import_router
    ├─ pdf → pdf_to_md_node → md_to_img_node → …
    └─ md  → md_to_img_node → …
```

### 面试要点
- **为什么要有入口节点**：统一校验 + 路由，避免每个下游节点自己判断后缀  
- **状态机思维**：节点只改 state，边决定走向（LangGraph 条件边）  
- **扩展点**：新增 `.docx` 等格式，优先改这里 + router，而不是改后面每个节点  

### 易错点
- 只改 flag 不够：PDF 还必须让下游拿到可解析路径；MD 直接给 `md_path` 跳过 MinerU  
- `file_dir` 与 `import_file_path` 都要校验，输出目录不存在会在后续节点炸  

---

## 2. PdfToMdNode（PDF → Markdown）

### 职责
把 PDF 解析成结构化 Markdown（含 `images/`），写入 `state['md_path']`，供图片节点 / 切分节点使用。

### 核心逻辑
1. 校验输入路径、输出目录  
2. 调用 `parse_doc` → `mineru.parse(..., tier="standard")`  
3. 约定输出：`{file_dir}/{stem}.md`  
4. 失败抛 `PdfConversionError`

### 今日澄清（重要）

#### （1）解析方式：不是纯传统 Pipeline
| 对比项 | 传统 Pipeline | 新一代纯 VLM | **本项目实际** |
|--------|---------------|--------------|----------------|
| 代表 | PDF-Extract-Kit 多小模型串行 | MinerU2.5 端到端 VLM | **Hybrid 高档** |
| 调用 | `backend=pipeline`（旧测试代码） | `vlm-*` | `tier="standard"` → effort=`high` |
| 本地模型 | `MinerU-4_models_torch`（Layout/OCR/Table…） | `MinerU2.5-Pro-*-1.2B` | **两套都有，高档会一起用** |

一句话：**小模型流水线 + VLM 混合，不是纯传统，也不是纯端到端 VLM。**

#### （2）有没有开子进程？
**没有。** 当前是同进程直接调 Python API。

- 代码里虽 `import subprocess`，注释也写着 CLI `mineru -p ...`，但实际走的是 `parse_doc()`  
- 面试指南里的 `subprocess.Popen` 是旧方案 / 理想写法，和现状不一致  

#### （3）要不要再开线程？
**一般不需要。**

- 导入整图已在 FastAPI `BackgroundTasks` 后台跑，接口不会被堵死  
- 节点内再开线程：下游仍要等解析完，链路不会更快  
- MinerU 是 CPU/GPU 重活：要隔离崩溃/内存 → 用**子进程**比线程更合适  

### 和下游 VLM 的区别（别混）
| | PdfToMd（MinerU） | MdToImg（Qwen-VL） |
|--|------------------|---------------------|
| 做什么 | PDF 版面 → Markdown | 图转文摘要，写回 MD |
| 何时 | 导入早期 | MinerU / 纯 MD 之后 |
| 模型 | MinerU Hybrid | 云端/API 视觉模型 |

### 面试要点
- **为何必须先转 MD**：后续切分、商品名、embedding 都是文本链路；多模态靠「图→文」降维  
- **为何要隔离（若问到）**：MinerU 吃内存、可能 OOM；子进程可保护主服务（现状未做）  
- **产出约定**：`md_path` + 同级 `images/`，是后面扫描图片的前提  

### 易错点
- 把「MinerU 里的 VLM」和「图片摘要 VLM」当成同一个东西  
- 以为 `BackgroundTasks` = 节点内多线程；其实只是整条导入任务进后台  
- 指南写子进程、代码写同进程 API —— 面试时要说清「现状」和「可优化点」  

---

## 3. 一句话串起来

上传落盘 → **Entry 判后缀、打路由标** →（PDF 则）**PdfToMd 用 MinerU Hybrid 出 MD** → 再进图片摘要 / 切分 / 向量化。

---

## 4. 可继续追问自己的题

1. 如果同时支持 Word，Entry 和 router 怎么改？  
2. `tier="flash"` / `"standard"` / `"advanced"` 分别适合什么文档？  
3. 要把 MinerU 改成子进程，接口怎么设计、如何回传 `md_path`？  
4. 解析失败时 state 回滚还是任务标记失败？现在怎么做的？  
