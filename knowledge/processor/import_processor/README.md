# Import Processor 知识框架与面试指南

> 范围：`knowledge/processor/import_processor`  
> 定位：把 PDF/MD 技术文档变成「可混合检索的切片向量库」

---

## 1. 一句话定位

基于 **LangGraph** 的文档入库 DAG：解析 → 多模态图转文 → 结构切分 → 商品名对齐 → BGE-M3 双向量 → 写入 Milvus。  
状态在节点间通过 `ImportGraphState` 传递，并由 `task_id` 驱动前端进度展示。

---

## 2. 管线总览

```text
entry_node
    ├─(PDF)→ pdf_to_md_node → md_to_img_node
    └─(MD)───────────────→ md_to_img_node
                              ↓
                     document_split_node
                              ↓
                  item_name_recognition_node
                              ↓
                     embedding_chunks_node
                              ↓
                       import_milvus_node
                              ↓
                             END
```

| 节点 | 职责 |
|------|------|
| `entry_node` | 入口校验与路由标志 |
| `pdf_to_md_node` | PDF → Markdown（MinerU） |
| `md_to_img_node` | 图片摘要 + MinIO + MD 回写 |
| `document_split_node` | 按标题切分 / 合并切片 |
| `item_name_recognition_node` | LLM 抽商品名并入库 |
| `embedding_chunks_node` | BGE-M3 混合向量化 |
| `import_milvus_node` | Schema / Index / 入库 |

编排入口：`main_graph.py`（`StateGraph` + 条件边 `import_router` + 顺序边）。

---

## 3. 状态机 ImportGraphState

| 字段类别 | 关键字段 | 作用 |
|----------|----------|------|
| 控制 | `is_pdf_read_enabled` / `is_md_read_enabled` | 条件边路由依据 |
| 路径 | `import_file_path` / `file_dir` / `md_path` | 节点间路径契约 |
| 内容 | `md_content` / `chunks` | 切分与嵌入的核心载体 |
| 元数据 | `file_title` / `item_name` | 过滤与商品对齐 |
| 追踪 | `task_id` | 前端 `/status` 进度轮询 |

默认值见 `state.py` 的 `GRAPH_DEFAULT_STATE`。

---

## 4. 逐节点拆解

### 4.1 entry_node

**作用：** 校验路径存在性，按后缀设置路由标志，提取 `file_title`。

**IO：**  
入：`import_file_path`, `file_dir`  
出：`is_pdf_read_enabled` / `is_md_read_enabled`, `pdf_path` / `md_path`, `file_title`

**知识点：**
- LangGraph 条件边：`import_router` 读标志决定下一跳
- `pathlib.Path`：`exists` / `suffix` / `stem`
- 前置校验：`StateFieldError` / `ValidationError`

**可追问：** 为什么用条件边而不是写死边？→ PDF/MD 入口不同，共用后续链路。

---

### 4.2 pdf_to_md_node

**作用：** 用 MinerU 把 PDF 解析成结构化 Markdown（含 `images/`）。

**IO：**  
入：`import_file_path`, `file_dir`  
出：`md_path`

**知识点：**
- 文档解析管线：版面分析 → MD + 图片目录
- 本地解析（MinerU local）与云端解析的取舍
- 输出约定：`{stem}.md` 与同级 `images/`

**可追问：** 为什么先转 MD？→ 统一下游切分与图片处理接口。

---

### 4.3 md_to_img_node

**作用：** 扫描 MD 中的图片，VLM 生成摘要，原图上传 MinIO，把图片引用替换为摘要文本。

**IO：**  
入：`md_path`  
出：`md_content`（摘要替换后）

**知识点：**
- 多模态 RAG：纯文本 embedding 吃不到图，需 VLM 转文本
- 上下文窗口：上下标题边界 + 段落级截取（就近原则）
- 限流：`deque` 滑动窗口控制 VLM RPM
- 对象存储：原图进 MinIO；检索侧依赖文本摘要
- 职责拆分：`ImageInfo` / `ImageContext` / Scanner / Summarizer

**可追问：** 为什么不直接多模态向量检索？→ 成本、链路复杂度，并与现有稠密/稀疏索引统一。

---

### 4.4 document_split_node

**作用：** 一级按 Markdown 标题切 chapter；二级对过长短切分、同源合并。

**IO：**  
入：`md_content`, `file_title`  
出：`chunks[{title, parent_title, file_title, content, ...}]`

**知识点：**
- 结构感知切分 > 纯固定长度：保留标题层级语义
- 代码围栏 `in_fence`：避免把 ` ``` ` 内的 `#` 当标题
- `hierarchy[1..6]` 追踪父标题，供同源合并
- 过长：`RecursiveCharacterTextSplitter` + 中英文分隔符
- 过短：`parent_title` 相同才合并，防止跨章污染
- 表格：`MarkdownTableLinearizer` 线性化，利于 embedding

**可追问：** `chunk_size` / `overlap` 如何权衡？→ 召回粒度 vs 上下文完整性；本项目 overlap 偏保守，靠标题元数据补偿。

---

### 4.5 item_name_recognition_node

**作用：** 从前 K 个 chunk 抽取商品名，BGE-M3 向量化后写入商品名集合，并回填到每个 chunk。

**IO：**  
入：`chunks`, `file_title`  
出：`item_name`；副作用：写入 `kb_item_names_v1`

**知识点：**
- 双集合设计：`item_names`（对齐）+ `chunks`（检索）
- 提示词约束命名（如不抽品牌），保证查询侧对齐
- 失败降级：`UNKNOWN` / 空结果时回退 `file_title`
- 为何向量库存商品名：语义对齐，而非 SQL LIKE

**可追问：** 用户说「RS-12」、库里是完整型号，如何对齐？→ 查询侧 `item_name_confirmed_node` 向量召回。

---

### 4.6 embedding_chunks_node

**作用：** 按 batch 对 chunk 做 BGE-M3 稠密 + 稀疏双向量。

**IO：**  
入：`chunks`  
出：`chunks[+dense_vector, +sparse_vector]`

**知识点：**
- 混合检索：dense = 语义相似；sparse ≈ 关键词精确（类 BM25）
- 嵌入文本：`item_name + content`，增强产品约束
- CSR 稀疏矩阵 → `{token_id: weight}` 字典入库
- MPS 兼容：COO 转 CSR（`indptr`）
- 批处理：`embedding_batch_size` 控显存/吞吐

**可追问：** 为何不用单一 dense？→ 型号/零件号等精确 token，sparse 更稳。

---

### 4.7 import_milvus_node

**作用：** 幂等建集合与索引，插入混合向量与标量元数据。

**IO：**  
入：带向量的 `chunks`  
出：写入 Milvus `kb_chunks_v1`

**知识点：**
- Schema：`chunk_id` PK、`dense` FLOAT_VECTOR、`sparse` SPARSE_FLOAT_VECTOR、标量元数据
- Index：dense `AUTOINDEX + COSINE`；sparse `SPARSE_INVERTED_INDEX + IP`
- 门面模式：SchemaBuilder / IndexBuilder / Inserter 职责分离
- 幂等：`has_collection` 则跳过创建
- 缺向量 chunk 跳过（数据级容错）

**可追问：** COSINE vs IP？→ 向量归一化后近似等价；稀疏常用 IP。动态字段 `enable_dynamic_field` 的利弊？

---

## 5. 数据落库模型

### kb_item_names_v1（商品名集合）

- 字段：`item_name` + dense/sparse + `file_title`
- 用途：查询侧商品名语义对齐

### kb_chunks_v1（切片集合）

- 向量：dense（COSINE）+ sparse（IP 倒排）
- 标量：`content` / `title` / `parent_title` / `file_title` / `item_name`

---

## 6. 横切架构知识点

### LangGraph 编排

- `StateGraph(ImportGraphState)` + TypedDict 共享状态
- 条件边 `import_router` vs 顺序边
- 节点可调用：`BaseNode.__call__` 统一日志 / 任务追踪 / 耗时
- `stream()` 逐节点事件，驱动前端 `/status` 轮询

### RAG 入库核心

```text
Parse → Enrich(图) → Chunk → Metadata(商品名) → Embed → Index
```

- 元数据贯穿：`title` / `parent_title` / `file_title` / `item_name`
- 混合向量为后续 `hybrid_search + WeightedRanker` 铺路

### 工程化

- `BaseNode` 模板方法：统一异常 `ImportProcessError`
- Config 集中 + dotenv；客户端单例 `AIClients` / `StorageClients`
- `task_id` 串联 running / done / duration，支撑 UI 进度

---

## 7. 面试常考问答

**Q1：导入链路整体怎么走？**  
上传落盘 → entry 路由 →（PDF 则 MinerU）→ VLM 图转文 → 标题感知切分 → LLM 商品名 → BGE-M3 双向量 → Milvus 入库。

**Q2：为什么要单独商品名集合？**  
查询时用户说法不完整，先在 `item_names` 做语义对齐，再用对齐后的名字过滤 `chunks`，减少串品。

**Q3：切分策略亮点？**  
结构优先（标题）+ 长度约束（递归切分）+ 同源合并（`parent_title`）+ 表格线性化。

**Q4：稠密 / 稀疏各自解决什么？**  
稠密抓同义与语义；稀疏抓型号、专有名词精确命中；入库后检索侧加权融合。

**Q5：和查询侧如何衔接？**  
导入写 `kb_item_names_v1` + `kb_chunks_v1`；查询走 `item_name_confirmed → hybrid/hyde search → rerank → 生成`。

**Q6：图片信息如何进入检索？**  
VLM 生成文本摘要写回 MD，再进入切分与 embedding；原图存 MinIO 供展示/溯源。

**Q7：BaseNode 解决了什么？**  
节点执行模板：统一日志、任务状态、耗时统计、异常包装，业务只实现 `process`。

**Q8：如何保证集合创建幂等？**  
`has_collection` 判断；已存在则跳过 schema/index 创建，只做数据插入。

---

## 8. 60 秒口述模板

1. 这是一个基于 LangGraph 的文档入库 DAG，状态在节点间传递。  
2. 先统一成 Markdown：PDF 用 MinerU；图片用 VLM 转摘要进文本链路，原图进 MinIO。  
3. 切分强调结构：标题切 → 过长短切 / 同源合并，并保留层级元数据。  
4. 商品名单独抽取并向量化，支撑查询对齐；切片用 BGE-M3 混合向量写入 Milvus。  
5. 工程上有 BaseNode 统一观测、配置与客户端单例、任务进度追踪。

---

## 9. 目录速查

| 文件 / 目录 | 说明 |
|-------------|------|
| `main_graph.py` | 图编排、条件边、编译入口 `import_app` |
| `state.py` | `ImportGraphState` 与默认状态 |
| `base.py` | 节点基类、日志与任务追踪 |
| `config.py` | 切分长度、集合名、模型与存储配置 |
| `exceptions.py` | 导入流程异常体系 |
| `mineru_parser.py` | MinerU 解析封装 |
| `nodes/` | 各业务节点实现 |

---

## 10. 总结

Import Processor 的核心价值不是「把文件塞进向量库」，而是：

1. **统一文档形态**（PDF/MD → 可切分 Markdown）  
2. **补齐多模态缺口**（图 → 文本摘要）  
3. **保留结构语义**（标题层级切分 + 元数据）  
4. **商品维度对齐**（独立商品名集合）  
5. **混合检索底座**（dense + sparse 写入同一 chunk）

面试时按「编排 → 解析增强 → 切分 → 元数据 → 向量 → 索引」这条主线展开，再按需下钻单个节点即可。
