# RAGAS 检索质量评测

对查询图谱产出的检索上下文计算：

- **Context Precision**：检出内容对回答是否有用、排序是否合理  
- **Context Recall**：标准答案要点能否被检索上下文覆盖  

默认取 `reranked_docs`（与线上喂给答案 LLM 的上下文一致）；可用 `--stage rrf` 对比粗排。

## 准备

```bash
cd knowledge
source .venv/bin/activate
pip install -r test/eval/ragas/requirements-eval.txt
```

确保 Milvus / 模型服务可用，且 `.env` 中 `OPENAI_API_KEY`、`OPENAI_API_BASE`、`LLM_DEFAULT_MODEL` 已配置（评判 LLM 复用同一套）。

可选：`RAGAS_JUDGE_MODEL` 单独指定评判模型。

## 评测集格式（JSONL）

```json
{"id": "demo_01", "question": "用户问题", "reference": "标准答案或要点"}
```

`sample_eval.jsonl` 仅为示例，请换成你知识库里真实可答的问题。

## 运行

在**仓库根目录**：

```bash
PYTHONPATH=. knowledge/.venv/bin/python \
  knowledge/test/eval/ragas/run_ragas_eval.py \
  --dataset knowledge/test/eval/ragas/sample_eval.jsonl \
  --stage reranked \
  --top-k 5 \
  --output knowledge/test/eval/ragas/ragas_report.json
```

常用参数：

| 参数 | 说明 |
|------|------|
| `--stage reranked\|rrf` | 用精排或 RRF 结果当 `retrieved_contexts` |
| `--top-k` | 送入 RAGAS 的上下文条数 |
| `--skip-short-circuit` | 跳过商品名确认失败、未进检索的样本 |

## 解读

- 商品名确认失败时 `retrieved_contexts` 为空，Precision/Recall 会很差——这是闸门行为，不是向量检索本身。  
- 对比实验：同一评测集分别跑 `--stage rrf` 与 `--stage reranked`，看精排增益。  
- 阈值/召回不理想时，优先扩评测集、检查 `item_names` 是否对齐，再调 RRF/Rerank。

## 注意

- 评判依赖 LLM，有费用与波动；建议固定小样本、`temperature=0`。  
- 当前环境用 `ragas==0.2.15` + 兼容 shim（见 `_compat.py`）。  
