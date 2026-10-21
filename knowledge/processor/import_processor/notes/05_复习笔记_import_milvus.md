# 复习笔记：ImportMilvusNode（import_milvus_node）

> 文件：`nodes/import_milvus_node.py`（219 行）
> 定位：导入流水线的最后一站。把上游已经带好 `dense_vector` / `sparse_vector` 的 chunks 落到 Milvus 的 `chunks` 集合，并把 Milvus 生成的主键回填到每条 chunk 上。

一句话：**校验并筛掉没向量的块 → 集合不在就建（schema + 索引）→ 一次性插入 → 主键回填。**

---

## 1. 节点在图谱中的位置

```text
document_split_node → item_name_recognition_node → embedding_chunks_node → import_milvus_node → END
```

- **输入**：`state['chunks']`，每块应含 `content / title / parent_title / file_title / item_name / dense_vector / sparse_vector`
- **输出**：`state` 原样返回，但 chunks 被**原地补上** `chunk_id`（Milvus 主键）
- **副作用**：`chunks_collection` 集合被创建（首次）并写入 N 行

到这里整条导入链就结束了，之后的数据由**查询侧**（`knowledge/query` 那条链）消费。

---

## 2. 整体流程（process）

```text
process(state)
 1. _validate_state(state)          → (validated_chunks, dim)
 2. StorageClients.get_milvus_client()   失败 → MilvusError（不降级）
 3. chunks_collection = config.chunks_collection
 4. _create_chunks_collection(...) 幂等，已存在直接 return
 5. _MilvusInserter.insert_rows(chunks)   插入 + 回填 chunk_id
 6. return state
```

与上游两个节点的错误策略对比（同一套流水线，三种态度）：

| 节点 | 失败时 | 理由 |
| --- | --- | --- |
| `item_name_recognition` | 降级到 `file_title` / 跳过入库 | 商品名是辅助信息 |
| `embedding_chunks` | 抛 `EmbeddingError` | 无向量 = 检索不到，致命 |
| `import_milvus` | 客户端失败抛 `MilvusError`；**单块缺向量则跳过** | 连接层致命，数据层可容错 |

---

## 3. `_validate_state` — 两级容错（本节点最值得学的设计）

```python
if not chunks or not isinstance(chunks, list):
    raise StateFieldError(...)              # ① 整体为空 → 直接失败

for i, chunk in enumerate(chunks):
    if not isinstance(chunk, dict):
        raise ValidationError(...)          # ② 单块类型错 → 直接失败（脏数据必须暴露）
    if chunk.get("dense_vector") and chunk.get("sparse_vector"):
        validated_chunks.append(chunk)      # ③ 向量齐全 → 收下
    else:
        self.logger.warning(f"chunks[{i}] 缺少混合向量，已跳过")   # ④ 缺向量 → 跳过 + 告警

if not validated_chunks:
    raise ValidationError("所有 chunk 均无有效向量，无法入库", self.name)   # ⑤ 全空 → 失败
```

**为什么「类型错要抛、缺向量要跳」**：类型错说明代码有 bug，必须炸出来；缺向量是**数据级**问题（某个 chunk 编码失败），丢这一块不影响其它块可用，只损失召回率，告警留痕即可。

### 3.1 向量维度是「推」出来的，不是写死的

```python
dim = len(validated_chunks[0]["dense_vector"])
```

建集合时的 `FLOAT_VECTOR(dim=dim)` 直接来自第一条有效 chunk 的实际长度，而不是读 `config.embedding_dim`。好处：换嵌入模型/维度时不用改两个地方；代价：**没有一致性校验**——如果第 2 条是 768 维、第 1 条是 1024 维，集合会按 1024 建，插入时 Milvus 才报错。

---

## 4. 四个内部组件（表驱动 + 单一职责）

| 组件 | 类型 | 职责 |
| --- | --- | --- |
| `_SCALAR_FIELD_SPC` | `@dataclass(frozen=True)` | 一条标量字段的规格：`field_name` / `datatype` / `max_length` |
| `_SCALAR_FIELDS` | `Sequence[_SCALAR_FIELD_SPC]` | 5 个标量字段的**声明式清单** |
| `_MilvusSchamaBuilder` | 静态方法类 | 按清单生成 schema |
| `_MilvusIndexBuilder` | 静态方法类 | 生成索引参数 |
| `_MilvusInserter` | 普通类（持有 client + collection） | 插入并回填主键 |

`ImportMilvusNode` 本身只做编排，类注释里写的「门面（门面摩丝）」是**门面模式**（Facade）的笔误——把建表、建索引、插入三个子系统藏在三个内部类后面，对外只暴露 `process`。

### 4.1 为什么要表驱动

```python
for spec in _SCALAR_FIELDS:
    kwargs = {"field_name": spec.field_name, "datatype": spec.datatype}
    if spec.max_length:
        kwargs["max_length"] = spec.max_length
    schema.add_field(**kwargs)
```

加字段只改 `_SCALAR_FIELDS` 元组，不用碰建表逻辑；`dict` 拼 `kwargs` 是为了 `INT64` 这类**不接受 `max_length`** 的类型不传空值（`max_length=None` 会报错）。

---

## 5. schema 细节

```python
schema = milvus_client.create_schema(enable_dynamic_field=True)
schema.add_field(field_name="chunk_id", datatype=DataType.INT64, is_primary=True, auto_id=True)
schema.add_field(field_name="dense_vector", datatype=DataType.FLOAT_VECTOR, dim=dim)
schema.add_field(field_name="sparse_vector", datatype=DataType.SPARSE_FLOAT_VECTOR)
# + 5 个标量
```

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `chunk_id` | `INT64`，`is_primary=True, auto_id=True` | 主键由 Milvus 生成，插入时**不要**传 |
| `dense_vector` | `FLOAT_VECTOR(dim)` | 维度从数据推断 |
| `sparse_vector` | `SPARSE_FLOAT_VECTOR` | `{token_id: weight}` |
| `content` | `VARCHAR(65535)` | chunk 正文（检索命中的就是它） |
| `title` / `parent_title` | `VARCHAR(65535)` | 章节层级，做上下文扩展用 |
| `file_title` | `VARCHAR(65535)` | 文档名，做过滤与溯源 |
| `item_name` | `VARCHAR(65535)` | 商品名，做过滤与语义锚点 |

**`enable_dynamic_field=True`**：允许插入 schema 之外的键，Milvus 会把它们塞进 `$meta`。好处是加字段不用重建集合；代价是动态字段**不能建索引、过滤性能差**、也没有类型约束。本项目所有插入键都已声明，所以这个开关当前属于「留给未来」的冗余能力。

`max_length=65535` 是 Milvus 对 VARCHAR 的常用上限，够放一整个 chunk。

---

## 6. 索引配置（与 item_name 集合完全一致）

```python
index.add_index(field_name="dense_vector",  index_name="dense_vector_index",
                index_type="AUTOINDEX",     metric_type="COSINE")
index.add_index(field_name="sparse_vector", index_name="sparse_vector_index",
                index_type="SPARSE_INVERTED_INDEX", metric_type="IP")
```

| 字段 | 索引类型 | 度量 | 原因 |
| --- | --- | --- | --- |
| dense | `AUTOINDEX` | `COSINE` | BGE-M3 输出已归一化，COSINE ≡ IP；AUTOINDEX 让 Milvus 按数据量自动选 HNSW/DiskANN 等 |
| sparse | `SPARSE_INVERTED_INDEX` | `IP` | 稀疏字段只支持 IP / BM25；倒排索引按 token 命中，天然适合词法匹配 |

**两个集合索引配置一模一样**，说明这是项目内统一的向量约定——面试可讲成「同一嵌入模型 → 同一度量口径，避免跨集合分数不可比」。

---

## 7. `_MilvusInserter.insert_rows` — 插入并回填主键

```python
inserted_result = self.milvus_client.insert(collection_name=self.collection_name, data=data)
chunk_ids = inserted_result.get('ids')
for chunk_id, chunk in zip(chunk_ids, data):
    chunk['chunk_id'] = chunk_id
```

- `auto_id=True` 时主键由服务端生成，返回值里的 `ids` **顺序与传入 data 一致**，所以可以直接 `zip` 回填。
- 回填的意义：后续若要做「按 chunk_id 更新/删除单条」「引用溯源点回到具体块」，手里得有主键；否则只能靠 `file_title` 模糊删。
- **原地修改**：`data` 就是 `state['chunks']` 里的同一批 dict 对象，所以 state 自动被更新，不需要再赋值回去。

---

## 8. 幂等：`has_collection` 只看「有没有」

```python
if milvus_client.has_collection(chunks_collection):
    self.logger.info(f"{chunks_collection}已存在，跳过创建")
    return
```

- 好处：重复跑同一份文档、重启服务都不会因「集合已存在」报错。
- 隐患：**只判断存在性，不比对 schema / 维度 / 索引**。如果换了嵌入模型导致 `dim` 变了，这里会静默跳过，把错误推迟到 `insert` 时才以「维度不匹配」爆出来，且报错信息离根因很远。

---

## 9. 两个集合的分工（对照 04 号笔记）

| | `item_name_collection` | `chunks_collection`（本节点） |
| --- | --- | --- |
| 由谁建 | `item_name_recognition_node` | `import_milvus_node` |
| 一条记录 | 一份文档 | 一个切片 |
| 主键 | `pk`：**VARCHAR(10) + auto_id** | `chunk_id`：**INT64 + auto_id** |
| 标量字段 | `file_title`、`item_name` | 5 个（含 content / title / parent_title） |
| 向量 | dense 1024 + sparse | dense `dim` + sparse（同款索引） |
| 检索用途 | 语义召回「用户在说哪台设备」→ 拿 `file_title` | 召回具体段落 → 喂给 LLM 作答 |

**先小集合定位文档，再大集合定位段落**——两级召回，避免在全量 chunk 里直接搜商品名导致噪声。

---

## 10. state 变化

### 10.1 进入本节点

```python
{
  "item_name": "优利德 UT890D+ 真有效值数字万用表",
  "chunks": [
    {"content": "产品概述\n\n…", "title": "产品概述", "parent_title": "产品手册",
     "file_title": "万用表的使用", "item_name": "优利德 UT890D+ …",
     "dense_vector": [1024 floats], "sparse_vector": {1234: 0.42, …}},
    …
  ]
}
```

### 10.2 离开本节点

同上，只是在每个 chunk 上多了一个键：

```python
{"chunk_id": 4611686018427387905, ...}
```

### 10.3 CLI 直跑（`_cli_main`）

```text
chunks_vector.json  →  ImportMilvusNode.process  →  chunks_vector_ids.json
```

`_cli_main` 做了一件贴心事：**兼容两种 JSON 结构**（根是 dict 取 `chunks`，根是 list 直接当 chunks），因为上游 `embedding_chunks_node.__main__` 存的是整个 `result_state`（dict），中间可能被手工裁过。

---

## 11. 查询侧怎么用这两个集合（延伸，面试常问）

导入只负责写，价值在**检索**时兑现。典型两步：

```python
# 第 1 步：商品名集合里语义召回，确定候选文档
q = embed_model.encode_queries([user_question])          # 注意是 queries 不是 documents
hits = client.search(
    collection_name=item_name_collection,
    data=[q["dense"][0].tolist()],
    anns_field="dense_vector",
    limit=5,
    output_fields=["file_title", "item_name"],
)
candidate_titles = {h["entity"]["file_title"] for h in hits[0]}

# 第 2 步：chunks 集合里做混合检索，用 file_title 收窄范围
reqs = [
    AnnSearchRequest(data=[q["dense"][0].tolist()],  anns_field="dense_vector",
                     param={"metric_type": "COSINE"}, limit=20),
    AnnSearchRequest(data=[q["sparse"][0]],          anns_field="sparse_vector",
                     param={"metric_type": "IP"},     limit=20),
]
res = client.hybrid_search(
    collection_name=chunks_collection,
    reqs=reqs,
    ranker=RRFRanker(60),                                 # 稠密/稀疏两路融合
    limit=10,
    filter=f'file_title in {list(candidate_titles)}',      # 用第一级结果收窄
    output_fields=["content", "title", "parent_title", "file_title"],
)
```

三个必须记住的点：

1. **建库用 `encode_documents`，检索用 `encode_queries`**——BGE-M3 的稀疏头在这两侧的词权重不完全等价，混用会掉召回（具体 API 形态按你的 pymilvus 版本核实）。
2. **`hybrid_search` 需要 `AnnSearchRequest` + `Ranker`**，两路分数不同量纲（COSINE ∈ [-1,1]、IP 无上界），必须靠 RRF 或 WeightedRanker 融合，不能直接相加。
3. **`filter` 走在标量字段上**：`file_title` / `item_name` 这类 VARCHAR 字段就是为此准备的；这也是它们 `max_length=65535` 而不是吝啬给 64 的原因之一。

---

## 12. 面试速记

**Q：为什么主键用 `auto_id` 而不是自己生成？**
省掉分布式 ID 生成逻辑，Milvus 内部保证唯一；代价是插入前拿不到 ID，只能插入后从返回值回填（就是 `_MilvusInserter` 干的事）。

**Q：为什么 `dense_vector` 的 `dim` 从数据推而不是读配置？**
配置里的 `embedding_dim` 和真实模型输出可能不同步；以数据为准能保证建表与数据一致。但这也放弃了提前发现维度不一致的机会。

**Q：`enable_dynamic_field=True` 有什么坑？**
动态字段可写但不可索引、过滤慢、无类型约束，且查询返回时包在 `$meta` 里。它适合「先用着，后面再改 schema」，不适合当主数据字段用。

**Q：为什么这个节点不做降级？**
Milvus 连不上就等于整条导入白跑，必须抛 `MilvusError` 让上层任务失败并重试；只有「个别 chunk 缺向量」这种局部问题才降级跳过。

**Q：插入为什么不用分批？**
当前一次导入的 chunk 数在几千量级，单次 insert 可接受。若要处理超大规模（十万级），应按 500～1000 行分批，避免单请求过大被服务端拒绝。

**Q：`has_collection` 幂等够吗？**
不够严格。它只保证「不因重复创建报错」，不保证 schema 一致；真正稳妥的做法是比较集合的 `describe_collection` 与预期 schema，不一致就显式报错或走迁移。

---

## 13. 易错 / 代码现状注意

1. **`StateFieldError` 位置参数错位（真 bug）**：
   ```python
   raise StateFieldError("待入库的 chunks 为空或类型无效", self.name)
   ```
   签名是 `(node_name, field_name, expected_type, message, cause)`，所以这里把中文消息当成了 `node_name`、把节点名当成了 `field_name`，最终消息会变成 `[待入库的 chunks 为空或类型无效] 状态字段 'import_milvus_node' 缺失或无效`。应改成 `StateFieldError(node_name=self.name, field_name="chunks", expected_type=list)`。
   （同文件里 `ValidationError(msg, self.name)` 的位置是对的，因为它的签名就是 `(message, node_name)`。）
2. **`dim` 只取第一条，全批不做一致性校验**：混维度数据会在 insert 阶段报错，且错误信息不指向具体行。
3. **集合已存在时不校验 schema / dim / 索引**：换模型后重复跑导入会静默复用旧集合。
4. **`insert_rows` 不分批**：`data` 多大就一次发多大；另外没有 try/except，插入异常直接冒泡（这在本节点是**期望行为**，但要知道它会让 state 里已回填的部分 `chunk_id` 留在内存里，虽然 state 不会落盘）。
5. **`chunk.get("dense_vector")` 的真值判断**：当前 `dense_vector` 是 `list`，空列表才算假，安全；如果哪天改成 `numpy.ndarray`，`if ndarray:` 会抛 `ValueError: truth value of an array is ambiguous`。
6. **`_SCALAR_FIELDS` 与 `item_name` 集合的 schema 是两套独立维护**：新增字段（如 `chunk_index`、`source_url`）要记得两边都改，否则检索侧拿不到。
7. 类注释「门面摩丝」应为「门面模式」；`_inserter` 这种带下划线的局部变量名与项目其它地方风格不一致（小事，但 Code Review 会被提）。

---

## 14. 一句话收束

**先按「类型错必炸、缺向量可跳」筛出有效块，用第一条的真实维度建集合（AUTOINDEX+COSINE / SPARSE_INVERTED_INDEX+IP），一次性插入并把自增主键回填到 chunk 上；两个集合同款索引配置，一个管「找哪份文档」，一个管「找哪段话」。**
