# 复习笔记：ItemNameRecognitionNode 与 EmbeddingChunksNode

> 文件：`nodes/item_name_recognition_node.py`（343 行）
> 文件：`nodes/embedding_chunks_node.py`（155 行）
> 定位：导入流水线的最后两个「填充语义」环节——先用 LLM 认出这堆切片是哪台设备，再把「设备名 + 切片正文」一起交给 BGE-M3 变成稠密 + 稀疏双向量，供 Milvus 入库与混合检索。

一句话分工：

| 节点 | 干的事 | 产出物 |
| --- | --- | --- |
| `ItemNameRecognitionNode` | LLM 从切片里抽出商品/设备名 → 名字向量化 → 单独存一个集合 | `state['item_name']`、每个 chunk 的 `item_name`、Milvus `item_name_collection` |
| `EmbeddingChunksNode` | 把 `item_name + content` 批量嵌入 | 每个 chunk 的 `dense_vector`、`sparse_vector` |

---

## 1. 节点在图谱中的位置

```text
entry_node ─┬→ pdf_to_md_node → md_to_img_node → document_split_node
            └→ md_to_img_node ─────────────────┘
                                                    ↓
                                    item_name_recognition_node   ← 本笔记
                                                    ↓
                                      embedding_chunks_node      ← 本笔记
                                                    ↓
                                        import_milvus_node → END
```

（边定义见 `main_graph.py` 的 `add_edge` 五连，`import_router` 只在入口处分叉 pdf / md）

- **上游给什么**：`document_split_node` 产出的 `chunks`，每块形如
  ```python
  {"content": "标题\n\n正文", "title": ..., "parent_title": ..., "file_title": ...}
  ```
- **本节点加什么**：`item_name`（字符串）、`dense_vector`、`sparse_vector`
- **下游要什么**：`import_milvus_node` 的标量字段声明里有 `item_name`，向量字段要 `dense_vector` / `sparse_vector`，所以这两个节点的字段名是**契约**，改名必须同步改 schema。

---

## 2. ItemNameRecognitionNode 整体流程

```text
process(state)
 1. _validate_state        取 file_title / chunks / item_name_chunk_k（默认 3），校验
 2. _prepare_llm_context   只取前 k 个 chunk 拼成上下文（省 token）
 3. _recognition_item_name 调 LLM 抽取商品名，失败逐级降级到 file_title
 4. _embedding_item_name   BGE-M3 → dense(1024) + sparse({token_id: weight})
 5. _insert_milvus         集合不存在先建（schema + 索引），再插一行
 6. _fill_item_name        回填 chunk['item_name'] 与 state['item_name']
```

相关配置（`config.py`）：

| 参数 | 默认 | 本节点用途 |
| --- | --- | --- |
| `item_name_chunk_k` | 3 | 送给 LLM 的切片条数 |
| `item_name_chunk_size` | 2500 | **本节点实际未使用**（定义了但没读） |
| `item_name_collection` | 环境变量 `ITEM_NAME_COLLECTION` | Milvus 集合名 |
| `embedding_dim` | 1024 | 与建集合时的 `dim` 必须一致 |

---

## 3. `_validate_state` — 参数校验

```python
file_title = state.get("file_title")      # 空 → StateFieldError
chunks     = state.get("chunks")          # 空 / 非 list → StateFieldError
item_name_chunk_k = self.config.item_name_chunk_k   # <=0 → ValidationError
```

要点：

- **只校验「能不能跑」，不做业务兜底**：`file_title` 缺失直接抛错，因为后面降级要靠它当商品名。
- 类型注解写成 `Tuple[str, List, int, int]`（4 元），**实际只返回 3 元**——注解笔误，不影响运行，但面试可主动指出。
- `chunks` 的 `expected_type=str` 也写错了，应该是 `list`（`embedding_chunks_node` 里就写对了）。

---

## 4. `_prepare_llm_context` — 上下文怎么拼

```python
for index, chunk in enumerate(chunks[:item_name_chunk_k]):
    if not isinstance(chunk, dict):
        continue
    content = chunk.get("content")
    splice_context = f"【切片】-f{index}- {content}"
```

- **只取前 3 块**：商品牌子/型号基本都在文档开头（封面、产品概述），不必喂全文，省 token 也降噪。
- `f"【切片】-f{index}- "` 里的 `f` 是**字面量字符**，不是格式符，实际输出 `【切片】-f0- 正文`。
- 非 dict 的脏块**跳过而不是抛错**，这里选择了宽松策略（与 `embedding_chunks_node` 的严格校验形成对比）。
- 返回是单个大字符串，`"\n"` 连接。

---

## 5. `_recognition_item_name` — LLM 抽取与降级链

### 5.1 提示词结构

- `ITEM_NAME_SYSTEM_PROMPT`：角色是「信息抽取接口」，四条规则 = 完整性（品牌+系列/型号+品类）、缺型号就退到品类、纯净输出、无法识别输出 `UNKNOWN`
- `ITEM_NAME_USER_PROMPT_TEMPLATE`：`{file_title}` + `{context}` 槽位，末尾 `商品名称：` 引导直接续写

### 5.2 四次降级（任何一环挂掉都不阻断整条流水线）

| 环节 | 异常 | 结果 |
| --- | --- | --- |
| 取 LLM 客户端 | `ConnectionError` | 直接 `return file_title` |
| 调 `invoke` | 任意 `Exception` | 记日志后 `return file_title` |
| 返回为空 或 `"UNKNOWN"` | — | 记日志后 `return file_title` |
| 正常 | — | 返回 `llm_result` |

也就是说：**商品名永远有值**，最差就是文件名（`万用表的使用` 这种）。这是「可用性优先」的设计——宁可商品名不准，也不能让整个导入任务失败。

### 5.3 一个细节坑

```python
llm_result = llm_response.content.strip("")
```

`strip("")` 的参数是**空字符串**，等于**什么都没剥**（`" abc \n".strip("")` 原样返回）。本意大概是去引号或空白，应写成 `.strip()` 或 `.strip('"').strip()`。
影响：模型若返回 `"优利德 UT890D+ 万用表"`（带引号），引号会一起进库、进向量。

---

## 6. `_embedding_item_name` — 单个商品名的双向量

```python
vector_result  = bge_m3_client.encode_documents(documents=[item_name])
dense_vector   = vector_result.get("dense")[0].tolist()      # 1024 维
sparse_csr     = vector_result.get("sparse")                 # scipy CSR 矩阵
if not hasattr(sparse_csr, "indptr"):
    sparse_csr = sparse_csr.tocsr()                          # MPS 下可能是 COO
start, end     = sparse_csr.indptr[0], sparse_csr.indptr[1]  # 第 0 行
token_id       = sparse_csr.indices[start:end].tolist()
weight         = sparse_csr.data[start:end].tolist()
sparse_vector  = dict(zip(token_id, weight))                 # {词id: 权重}
```

关键点：

1. **为什么单条也要走 `encode_documents([...])`**：BGE-M3 的文档侧编码 API，传 list 返回 dict（`dense` 二维数组 / `sparse` CSR），即使 1 条也保持批量接口，代码路径与 `EmbeddingChunksNode` 一致。
2. **COO→CSR 兼容**：Apple MPS 后端下 `sparse` 可能返回 COO（没有 `indptr`），必须 `tocsr()`。两个节点都有这段防御，属于踩过的坑。
3. **CSR 三数组**：`indptr`（行偏移，长度 = 行数+1）、`indices`（列号 = token_id）、`data`（权重）。取第 i 行 → `indptr[i] : indptr[i+1]`。
4. **存成 dict 而不是两个 list**：Milvus 稀疏向量字段的插入格式就是 `{token_id: weight}`，直接对应。
5. 失败（客户端建不出 / 编码抛错）统一返回 `(None, None)`，由下游 `_insert_milvus` 判断后静默跳过。

---

## 7. `_insert_milvus` + `_create_item_name_collection` — 单独的商品名集合

### 7.1 为什么单独存一个集合

MySQL 的 `LIKE '%型号%'` 只能字面匹配，用户说「那个优利德的数字万用表」查不到 `UT890D+`。所以要一条 **商品名 → 文档** 的语义索引：先在这个小集合里按语义找到最像的商品名，再拿 `file_title` 去 chunks 集合里捞正文。

```text
用户问题 ──→ item_name 集合（语义召回商品名）──→ file_title ──→ chunks 集合（正文召回）
```

### 7.2 建集合（幂等）

```python
if not milvus_client.has_collection(item_name_collection_name):
    self._create_item_name_collection(...)
```

`has_collection` 做幂等，避免重复建报错——这也是「先建表后插入」的通用写法。

### 7.3 schema

| 字段 | 类型 | 约束 |
| --- | --- | --- |
| `pk` | `VARCHAR(10)` | `is_primary=True, auto_id=True` |
| `file_title` | `VARCHAR(65535)` | 标量 |
| `item_name` | `VARCHAR(65535)` | 标量 |
| `dense_vector` | `FLOAT_VECTOR(dim=1024)` | 稠密 |
| `sparse_vector` | `SPARSE_FLOAT_VECTOR` | 稀疏 |

### 7.4 索引与度量（面试高频）

| 字段 | index_type | metric_type | 为什么 |
| --- | --- | --- | --- |
| `dense_vector` | `AUTOINDEX` | `COSINE` | BGE-M3 输出已归一化，**COSINE 与 IP 等价**；换未归一化的模型两者就不等了 |
| `sparse_vector` | `SPARSE_INVERTED_INDEX` | `IP` | 稀疏向量**只支持 IP 与 BM25** |

Milvus 三大概念（代码注释里也写了一段，值得背）：

- **Collection**：数据的容器（≈ MySQL 表）
- **Schema**：字段约束（≈ 字段类型/长度）
- **Index**：加速检索的算法结构（≈ B+ 树/Hash，Milvus 里是图/倒排）

使用 Milvus 固定三步：**建集合（schema + index）→ 插数据 → 查/检索**。

### 7.5 插入行

```python
item_name_data_row = {
    "file_title": file_title,
    "item_name": item_name,
    "dense_vector": dense_vector,      # List[float], 1024
    "sparse_vector": sparse_vector,    # Dict[int, float]
}
```

`data=[row]` 传的是**列表包一行**——Milvus 批量插入接口，单条也要包一层。

---

## 8. `_fill_item_name` — 两个位置都要回填

```python
for chunk in chunks:
    chunk["item_name"] = item_name   # ① 给下游 embedding / milvus 用
state["item_name"] = item_name       # ② 给其它节点 / 接口返回用
```

**为什么 chunk 级也要写**：`EmbeddingChunksNode` 拼嵌入文本时读的就是 `chunk["item_name"]`，不写这里，第二个节点拿不到商品名，chunk 就会丢失这层语义。

---

## 9. EmbeddingChunksNode 整体流程

```text
process(state)
 1. _validate_state    chunks 必须是非空 list，且每个元素都是 dict（严格）
 2. AIClients.get_bge_m3_client()   失败 → EmbeddingError（熔断，不降级）
 3. for batch in range(0, total, batch_size=8):
        _embed_chunks(batch)  → 写 dense_vector / sparse_vector
 4. state["chunks"] = final_chunks
```

**注意两节点错误策略的差别**：

| 节点 | 失败时 | 理由 |
| --- | --- | --- |
| `item_name_recognition` | 降级（用 file_title / 跳过入库） | 商品名是「锦上添花」 |
| `embedding_chunks` | 抛 `EmbeddingError` | 没有向量 = 这批数据检索不到，属于致命错误 |

---

## 10. `_embed_chunks` — 批量嵌入（重点）

### 10.1 嵌入文本的拼法

```python
embedding_documents = [
    f"{chunk.get('item_name', '')}\n{chunk.get('content', '')}"
    for chunk in batch_chunks
]
```

**这是整套设计的核心技巧**：把商品名放在正文前面一起编码。

- 「更换电池时请先断开电源」这种块，脱离上下文根本不知道是哪台设备；
- 前面加上 `优利德 UT890D+ 数字万用表`，整块就带上了主体语义，用户问「万用表怎么换电池」才能召回；
- 用 `\n` 分隔而不是空格，保留「标题行 / 正文」的结构感；
- `get(..., '')` 双保险：即使上游没回填 `item_name` 也不会 KeyError，最多退化成只嵌正文。

> 副作用要清楚：同一段正文被挂到不同商品名下会得到不同向量，这是**故意的**——语义本来就不同。

### 10.2 批量编码与逐条拆分

```python
embed_vector = embed_model.encode_documents(embedding_documents)   # 整批一次
sparse_csr   = embed_vector.get('sparse')
if not hasattr(sparse_csr, 'indptr'):
    sparse_csr = sparse_csr.tocsr()                                # MPS 兼容

for i, chunk in enumerate(batch_chunks):
    chunk['dense_vector']  = embed_vector.get('dense')[i].tolist()
    chunk['sparse_vector'] = self._extract_sparse_vector(sparse_csr, i)
```

- **`i` 是批内下标，不是全局下标**：`sparse_csr` 是这一批的矩阵，行数 = 本批条数，用全局 index 会越界或错位。这是最容易写错的一行。
- `dense[i]` 是 numpy 行向量，`.tolist()` 转 Python list 才能给 pymilvus。

### 10.3 `_extract_sparse_vector` 与单条版的区别

| | `item_name_recognition._embedding_item_name` | `embedding_chunks._extract_sparse_vector` |
| --- | --- | --- |
| 行号 | 写死 `indptr[0] / indptr[1]` | 参数化 `indptr[index] / indptr[index+1]` |
| 输入 | 单条 | 一批 |
| 复用性 | 只能处理 1 条 | 通用 |

两条路径本质相同：**CSR 第 i 行 = `indptr[i]` 到 `indptr[i+1]` 之间的 `(indices, data)` 配对**。

---

## 11. 两个节点串起来的数据流

### 11.1 输入 state（document_split 之后）

```python
{
  "file_title": "万用表的使用",
  "chunks": [
    {"content": "产品概述\n\n优利德 UT890D+ 是一款真有效值数字万用表…",
     "title": "产品概述", "parent_title": "产品手册", "file_title": "万用表的使用"},
    {"content": "更换电池\n\n打开后盖…", "title": "更换电池", "parent_title": "维护", "file_title": "万用表的使用"}
  ]
}
```

### 11.2 `item_name_recognition_node` 之后

```python
{
  "file_title": "万用表的使用",
  "item_name": "优利德 UT890D+ 真有效值数字万用表",     # ← 新增
  "chunks": [
    {"content": "...", "title": "产品概述", ..., "item_name": "优利德 UT890D+ 真有效值数字万用表"},  # ← 每块回填
    ...
  ]
}
# 侧路：Milvus item_name 集合多一行 {file_title, item_name, dense, sparse}
```

### 11.3 `embedding_chunks_node` 之后

```python
{
  "item_name": "...",
  "chunks": [
    {"content": "...", "item_name": "...", "title": "...",
     "dense_vector": [0.013, -0.204, ...],          # 1024 维
     "sparse_vector": {1234: 0.42, 98765: 0.11, ...}} # {token_id: weight}
  ]
}
```

### 11.4 为什么是「两个集合」而不是一个

| 集合 | 一条记录代表 | 检索用途 |
| --- | --- | --- |
| `item_name_collection` | 一份文档 | 从「用户怎么叫这台设备」定位到文档 |
| `chunks_collection`（下游入库） | 一个切片 | 从「具体问题」定位到段落 |

粒度不同、召回目的不同，混在一个集合里会互相稀释。

---

## 12. BGE-M3 为什么给两个向量

| 向量 | 抓什么 | 强项 | 弱项 |
| --- | --- | --- | --- |
| dense（1024 维） | 语义 | 同义改写、跨语言、口语化提问 | 型号/编号等罕见串不敏感 |
| sparse（token 权重） | 词法 | 精确命中 `UT890D+`、`S7-1200` 这类专有串 | 换个说法就丢 |

两个一起用 = **hybrid search**：Milvus 侧对两路结果做 `RRFRanker` / `WeightedRanker` 融合。这就是选 BGE-M3 而不是纯 dense 模型的原因——商品文档里型号是硬信息，纯语义容易糊。

> token_id 具体来自 BGE-M3 稀疏头对应的词表（细节需核实）；对本项目只需知道「它是词 id，不是字符位置」。

---

## 13. 端到端小例子

```text
1. 用户上传《万用表的使用.pdf》
2. 切出 12 个 chunk（首块含"优利德 UT890D+"）
3. item_name_recognition：
   - 取前 3 块 → LLM → "优利德 UT890D+ 真有效值数字万用表"
   - 编码成 dense + sparse → 插入 item_name 集合（当前文档 1 行）
   - 12 个 chunk 全部写入 item_name
4. embedding_chunks：按 8 条一批
   - 第 1 批 8 条 → 一次 encode_documents → 拆 8 组向量
   - 第 2 批 4 条 → 同上
   - 12 个 chunk 都带上 dense / sparse
5. import_milvus：把带向量的 chunk 写进 chunks 集合
```

---

## 14. 面试速记

**Q：为什么商品名要单独建一个 Milvus 集合？**
MySQL 模糊查询没有语义，用户说的「优利德那个万用表」匹配不到 `UT890D+`。单独一份「商品名小集合」做语义入口，召回 `file_title` 后再去 chunks 集合捞正文，是两级召回。

**Q：chunk 嵌入为什么要把 item_name 拼在 content 前面？**
切片脱离全文会丢主体，「更换电池」这种块单独看不知道是哪台设备。拼上商品名等于给每个块补了主体语义，跨块提问才召得回。

**Q：为什么同时要稠密和稀疏两种向量？**
dense 抓语义改写，sparse 抓型号/编号这类精确串；商品文档里两者都不能少，Milvus 侧再融合。

**Q：COSINE 和 IP 什么时候等价？**
向量归一化后等价。BGE-M3 输出已归一化所以选 COSINE 没问题；换成未归一化的模型就必须区分。

**Q：稀疏向量为什么只能用 IP / BM25？**
Milvus 稀疏索引（`SPARSE_INVERTED_INDEX`）的设计只支持这两种度量，它算的是加权内积式的相关度。

**Q：为什么要 COO→CSR？**
MPS 后端下 scipy 稀疏矩阵可能返回 COO（无 `indptr`），而取行需要 CSR 的行偏移结构。两处代码都做了 `hasattr` 判断后 `tocsr()`。

**Q：批量嵌入的 batch_size 取 8 是什么考虑？**
显存/内存与吞吐的折中；太大容易 OOM，太小浪费编码器并行度。这里是配置项 `embedding_batch_size`，可调。

**Q：为什么 embedding 失败要抛异常，商品名失败却降级？**
没有向量 = 数据检索不到，属于必须重试的致命错误；商品名只是个辅助字段，用文件名兜底还能跑。

---

## 15. 易错 / 代码现状注意

1. **`ItemNameRecognitionNode` 没有类属性 `name`**：`process` 里写了 `name = "item_name_recognition_node"` 但那是**局部变量**，`self.name` 仍是基类默认的 `base_node`。后果：日志 logger 名变成 `import.base_node`，`StateFieldError(node_name=self.name)` 报的也是 `base_node`。
2. **`_insert_milvus` 有 `UnboundLocalError` 风险**：`insert_result` 在 `try` 内赋值，`except` 只记日志不 return，第 237 行却在 `try` 外读 `insert_result.get('ids')`——插入抛异常时这里会二次崩。
3. **`strip("")` 无实际效果**（见 5.3），模型带引号返回时会污染入库值。
4. **`item_name_chunk_size = 2500` 定义了没用**：注释说「商品名识别时使用的切片内容长度」，实际只按条数 `k` 截取，没按字符数截断，长块可能撑大 prompt。
5. **`_validate_state` 注解 4 元实际返回 3 元**，`chunks` 的 `expected_type=str` 也应为 `list`。
6. **`_embed_chunks` 原地修改 chunk**：`chunk['dense_vector'] = ...` 直接改上游传入的 dict，`final_chunks` 与 `state['chunks']` 是同一批对象引用。功能上没问题（正是想要的效果），但要知道「不是拷贝语义」。
7. **`if not embed_vector` 判空偏弱**：`encode_documents` 返回 dict，理论上缺 `dense` 键时会 `KeyError` 而不是走这个分支。
8. **`item_name_recognition` 对 chunks 宽松、`embedding_chunks` 严格**：同一份数据两处校验标准不同，脏块在前者被静默跳过，在后者会直接抛错。

> **2026-10-21 更新**：第 1、2、3、5 条已修复并提交本仓库——补上类属性 `name`、`insert_result` 预初始化 + `except` 中 `return`、`strip("")` 改为 `.strip().strip('"“”').strip()`、`_validate_state` 注解改为 `Tuple[str, List, int]` 且 `expected_type=list`。第 4、6、7、8 条仍保持现状（`item_name_chunk_size` 未使用 / 原地修改 / 判空偏弱 / 两节点校验口径不一，属待议的设计取舍，未改动）。

---

## 16. 一句话收束

**LLM 先给整篇文档定一个「它是什么设备」，这个名字既进独立的小集合当语义入口，又贴到每个切片头上一起编码；BGE-M3 一次前向同时产出稠密（语义）与稀疏（型号精确匹配）双向量，按 8 条一批切开写回 chunk，最后由 import_milvus 落库。**
