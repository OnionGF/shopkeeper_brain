# Query Processor 知识框架与面试指南

> 范围：`knowledge/processor/query_processor`  
> 配套：`knowledge/utils/sse_util.py`、`knowledge/utils/task_util.py`、`knowledge/shcemal/query_service.py`  
> 定位：商品知识库问答——商品名对齐 → 多路检索融合 → 精排 → 答案生成，并通过 SSE 实时推给前端

---

## 1. 一句话定位

基于 **LangGraph** 的查询 DAG：先确认用户问的是哪款商品，再并行走本地混合检索 / HyDE / 联网搜索，经 RRF 融合与 Rerank 精排后，由答案节点生成回复。  
流式场景下，各节点是**生产者**，SSE 队列是缓冲，API/`EventSource` 是**消费者**。

---

## 2. 管线总览

```text
item_name_confirmed_node
        │
        ├── (已有 answer) ─────────────────────→ answer_output_node → END
        │
        └── (无 answer，商品已确认)
                 │
                 v
            multi_search（虚节点，扇出）
                 │
       ┌─────────┼─────────┐
       v         v         v
   hybrid     hyde      web_mcp
       │         │         │
       └─────────┼─────────┘
                 v
               join（虚节点，汇合）
                 │
                 v
           rrf_merge_node
                 │
                 v
           reranker_node
                 │
                 v
         answer_output_node → END
```

| 节点 | 职责 |
|------|------|
| `item_name_confirmed_node` | LLM 抽商品名 + Milvus 对齐 + 决策（检索 / 澄清 / 抱歉） |
| `multi_search` / `join` | 扇出 / 汇合虚节点，实现三路并行 |
| `hybrid_vector_search_node` | 查询向量混合检索（dense+sparse）+ `item_name` 过滤 |
| `hyde_vector_search_node` | HyDE：先生成假设文档再检索 |
| `web_mcp_search_node` | 百炼 MCP 联网搜索 |
| `rrf_merge_node` | 本地两路结果 RRF 融合去重 |
| `reranker_node` | 本地 + 网页文档交叉精排，截断 top-k |
| `answer_output_node` | 组 prompt、调 LLM、流式/非流式推送、写历史 |

编排入口：`main_graph.py`（`query_app`）。

---

## 3. 状态机 QueryGraphState

| 字段类别 | 关键字段 | 作用 |
|----------|----------|------|
| 会话 | `session_id` / `task_id` | 历史对话、SSE/任务追踪 |
| 查询 | `original_query` / `rewritten_query` / `item_names` | 改写与过滤 |
| 检索 | `embedding_chunks` / `hyde_embedding_chunks` / `web_search_docs` | 三路原始结果 |
| 融合 | `rrf_chunks` / `reranked_docs` | 粗排 → 精排 |
| 生成 | `prompt` / `answer` / `history` | 答案与落库 |
| 控制 | `is_stream` | 是否走 SSE 增量输出 |

路由关键：`route_after_item_confirm` 看 `state["answer"]` 是否已有——有则短路到答案节点。

---

## 4. 逐节点拆解

### 4.1 item_name_confirmed_node

**作用：** 从问题（+历史）提取商品名并改写查询；用 `kb_item_names` 向量对齐；决策后续走哪条路。

**三分支决策：**

| 容器 | 含义 | 行为 |
|------|------|------|
| `confirmed` | 高置信对齐成功 | 写入 `item_names`/`rewritten_query`，**不写 answer**，继续三路检索 |
| `options` | 中置信多个候选 | 写 `answer` 让用户确认商品 → **短路**到答案节点 |
| 都空 | 无法识别 | 写抱歉文案到 `answer` → **短路** |

**知识点：**
- 导入侧写完整商品名，查询侧用户说法常不完整 → 必须向量对齐，不能只靠字符串相等
- 阈值：`item_name_high_confidence` / `item_name_score_gap` / `item_name_max_options`（可压测调参）
- 对齐目标是 **Milvus 里的名字**（chunk 上也挂这个名字），否则下游 `item_name in [...]` 过滤会空召回

**可追问：** 为什么不直接用 LLM 抽出的名字去滤 chunks？→ 与库内字段不一致会产生大量噪声，放大幻觉。

---

### 4.2 hybrid_vector_search_node

**作用：** 对 `rewritten_query` 做 BGE-M3 混合向量，在 `kb_chunks` 上 hybrid search，并按 `item_names` 精确过滤。

**知识点：**
- dense 语义 + sparse 关键词；`WeightedRanker` 融合
- 过滤表达式：`item_name in {item_names}`（依赖上游对齐质量）
- 空结果时可不写 `embedding_chunks`（注意测试入口对 `None` 的防护）

---

### 4.3 hyde_vector_search_node

**作用：** HyDE（Hypothetical Document Embeddings）——先让 LLM 生成「像文档的假想答案」，再对该文本 embedding 检索。

**知识点：**
- 解决「短问句 ↔ 长说明文档」语义鸿沟
- 与 hybrid 同库不同查询表示，提升召回多样性，再交给 RRF

**可追问：** HyDE 的代价？→ 多一次 LLM 调用；假想文档偏题时会引入噪声，靠 RRF/Rerank 兜底。

---

### 4.4 web_mcp_search_node

**作用：** 通过 DashScope WebSearch MCP（`bailian_web_search`）补外部网页片段。

**知识点：**
- Streamable HTTP MCP；鉴权 Bearer API Key
- 注意 `mcp` SDK 大版本与百炼协议兼容（项目侧建议 `mcp<2`）
- 结果进 `web_search_docs`，不参与 RRF，直接进 Rerank 与本地结果混排

---

### 4.5 rrf_merge_node

**作用：** 对 hybrid / hyde 两路本地结果做 Reciprocal Rank Fusion。

**公式（概念）：**  
`score(d) += weight / (k + rank(d))`

**知识点：**
- 按 `chunk_id` 去重累加；按分数排序截断 `rrf_max_results`
- `k` 平滑参数影响大于小幅 weight 调整
- 输出 `rrf_chunks`，供精排使用

**可追问：** 为什么不用分数直接相加？→ 不同检索路的绝对分不可比，用排名融合更稳健。

---

### 4.6 reranker_node

**作用：** 收集本地 RRF 结果 + 网页结果，用 BGE Reranker 交叉打分，再 cliff cutoff 取 top-k。

**知识点：**
- 双塔召回便宜、交叉精排贵但准 → 典型「召回+精排」两段式
- sigmoid 归一化分数；`rerank_min_top_k` / `rerank_max_top_k` 控上下文长度
- 过大：噪声进 LLM；过小：漏关键步骤

---

### 4.7 answer_output_node（重点，对应 SSE 图）

**作用：** 查询图终点——组提示词、调用 LLM、按流式策略推送、写入 Mongo 历史。

**内部两条路径：**

```text
state 已有 answer？
  ├─ 是（澄清/抱歉短路）
  │     非流式 → set_task_result(answer)
  │     流式   → 最后 FINAL 时带上完整 answer
  └─ 否（正常生成）
        拼 ANSWER_PROMPT(context + history + item_names + question)
        is_stream=True  → llm.stream() → 每个片段 DELTA → FINAL({})
        is_stream=False → llm.invoke() → set_task_result(answer)
```

**知识点：**
- 上下文预算：`max_context_chars`，检索上下文与历史按字符配额瓜分
- 元数据拼进 prompt（chunk_id / title / source / url / score）利于可追溯回答
- 历史：`save_chat_message` 写入 Mongo（user + assistant）

---

## 5. 生产者-消费者与 SSE（结合答案节点）

### 5.1 架构图映射

```text
[生产者] Query 各节点 process / __call__
        │  push_sse_event / set_task_result
        ▼
[中间件] SSE 队列(_task_stream) + 任务容器(task_util)
        │  sse_generator 消费
        ▼
[消费者] GET /stream/{task_id} → 前端 EventSource
```

| 图中概念 | 代码 |
|----------|------|
| 其它节点推进度 | `BaseNode.__call__` → `progress` |
| 答案节点推增量/终态 | `answer_output_node` → `delta` / `final` |
| SSE 队列 | `sse_util._task_stream[task_id]` |
| 运行中/已完成/状态/结果 | `task_util` 各容器 |
| 跑图 | `QueryService.run_query_graph` → `query_app.invoke` |
| 读流 | `sse_generator` + 前端 `EventSource` |

### 5.2 三种事件

| 事件 | 谁推 | 含义 | 前端 |
|------|------|------|------|
| `progress` | 每个节点 `__call__`（仅 `is_stream`） | 进度快照：status / done / running | 更新节点进度面板 |
| `delta` | 仅答案节点 `_stream_llm` | LLM 文本增量 | 打字机拼接 |
| `final` | 仅答案节点末尾 | 本轮查询结束 | 关连接、定稿、收起进度 |

**约定：** 若答案已由 stream 吐完，`FINAL` 常为 `{}`；若短路答案未经 delta，`FINAL` 携带完整 `answer`。

### 5.3 流式 vs 非流式

| 模式 | 答案去哪 | 进度 |
|------|----------|------|
| `is_stream=True` | SSE：`delta` + `final` | 各节点 `progress` |
| `is_stream=False` | `set_task_result` → 结果容器 | 一般不推 SSE |

### 5.4 端到端时序（流式）

```text
POST /query {query, is_stream:true}
  → task_id，create_sse_queue(task_id)
  → 后台 invoke 查询图

GET /stream/{task_id}
  → sse_generator 读队列并 yield SSE 包

节点执行：progress ... →（答案节点）delta ... → final
前端收到 final → 关闭 EventSource
```

---

## 6. 与导入侧的衔接

| 导入侧产物 | 查询侧用法 |
|------------|------------|
| `kb_item_names_v1` | 商品名语义对齐 |
| `kb_chunks_v1`（dense+sparse+item_name 等） | hybrid / hyde 检索 + 过滤 |
| MinIO 原图 | 答案中图片 URL / 展示（若有） |
| 商品名命名规范（如不抽品牌） | 降低用户说法与库内名的鸿沟 |

---

## 7. 横切架构知识点

### LangGraph

- 条件边短路：商品未确认时跳过昂贵三路检索
- 扇出/汇合：`multi_search` / `join` 虚节点表达并行
- `BaseNode.__call__`：统一日志、running/done、流式 progress

### RAG 查询范式

```text
意图/实体对齐 → 多路召回 → 排名融合 → 交叉精排 → 生成
```

- 召回要全（hybrid + hyde + web），精排要准（reranker），生成要控上下文长度

### 工程化

- 任务维度隔离：所有队列/状态以 `task_id` 为键
- SSE 与业务解耦：节点只 `push`，不感知 HTTP
- 会话历史在 Mongo，支撑多轮改写与指代消解

---

## 8. 面试常考问答

**Q1：查询链路整体怎么走？**  
商品名提取对齐 → 确认则三路检索 → RRF（本地两路）→ Rerank（本地+网页）→ 答案生成；不确认则短路返回澄清/抱歉。

**Q2：为什么要商品名对齐？**  
导入写的是库内标准名，用户常说简称；不对齐则 `item_name` 过滤失效或噪声大。

**Q3：三路检索各自解决什么？**  
Hybrid：常规语义+关键词；HyDE：问句-文档鸿沟；Web：库外时效/补充信息。

**Q4：RRF 和 Rerank 区别？**  
RRF 是多路排名融合（便宜、无监督）；Rerank 是 query-doc 交叉打分（贵、准），裁剪进 LLM 的上下文。

**Q5：SSE 里 progress / delta / final 谁负责？**  
progress：所有节点基类；delta/final：只有答案节点。final 表示整轮结束。

**Q6：答案节点何时不调 LLM？**  
上游已写入 `answer`（澄清选项或抱歉）时，只负责推送与存历史。

**Q7：流式与非流式如何并存？**  
同一 `process`，用 `is_stream` 分支：`stream+push DELTA` vs `invoke+set_task_result`。

**Q8：生产者消费者怎么解耦？**  
节点写内存队列，API 用 `sse_generator` 读队列打包 SSE；前端 EventSource 订阅，互不阻塞。

---

## 9. 60 秒口述模板

1. 查询是 LangGraph DAG：先对齐商品，不确定就短路问用户。  
2. 确认后并行 hybrid / HyDE / 联网，本地两路 RRF，再和网页一起 Rerank。  
3. 答案节点组上下文调 LLM；开流式时经 SSE 推 delta，最后 final。  
4. 其它节点只推 progress；任务状态与结果按 task_id 隔离。  
5. 和导入衔接：双集合 + 混合向量，保证过滤与召回一致。

---

## 10. 目录速查

| 文件 / 模块 | 说明 |
|-------------|------|
| `main_graph.py` | 图编排、条件边、并行扇出、`query_app` |
| `state.py` | `QueryGraphState` |
| `base.py` | 节点基类 + progress 推送 |
| `nodes/answer_output_node.py` | 生成答案 + delta/final |
| `nodes/item_name_confirmed_node.py` | 抽取、对齐、决策 |
| `utils/sse_util.py` | SSE 队列与 generator |
| `utils/task_util.py` | 任务进度/状态/结果容器 |
| `shcemal/query_service.py` | 跑图与取结果服务 |
| `front-agent/` | React 前端：EventSource 消费 progress/delta/final |

---

## 11. 总结

Query Processor 的核心价值不是「调一次 LLM」，而是：

1. **先对齐实体**，避免带错商品检索  
2. **多路召回 + 融合 + 精排**，控噪声再生成  
3. **答案节点统一出口**，兼容短路文案与 LLM 生成  
4. **SSE 生产者-消费者**，进度与打字机体验和业务图解耦  

面试时按「对齐 → 召回 → 融合 → 精排 → 生成 → 推送」展开，再按需下钻 SSE 三种事件与答案节点分支即可。
