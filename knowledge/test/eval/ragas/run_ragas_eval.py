#!/usr/bin/env python3
"""用 RAGAS 评估本项目 RAG 检索质量（Context Precision / Context Recall）。

用法（在仓库根目录）::

    PYTHONPATH=. knowledge/.venv/bin/python \\
      knowledge/test/eval/ragas/run_ragas_eval.py \\
      --dataset knowledge/test/eval/ragas/sample_eval.jsonl

评测集 JSONL 每行字段：
  - id: 可选
  - question: 用户问题（必填）
  - reference: 标准答案 / 要点（必填，供 RAGAS 评判）
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import uuid
from pathlib import Path
from typing import Any, Dict, List, Literal

# 仓库根目录
_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from dotenv import load_dotenv

load_dotenv(_REPO_ROOT / "knowledge" / ".env")

from knowledge.test.eval.ragas._compat import ensure_ragas_imports

ensure_ragas_imports()

from datasets import Dataset
from langchain_openai import ChatOpenAI
from ragas import evaluate
from ragas.llms import LangchainLLMWrapper
from ragas.metrics import context_precision, context_recall

from knowledge.processor.query_processor.main_graph import query_app
from knowledge.processor.query_processor.state import create_default_state

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("ragas_eval")

ContextStage = Literal["reranked", "rrf"]


def _load_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as e:
                raise ValueError(f"{path}:{line_no} JSON 解析失败: {e}") from e
            if not obj.get("question") or not obj.get("reference"):
                raise ValueError(f"{path}:{line_no} 需要 question 与 reference 字段")
            rows.append(obj)
    if not rows:
        raise ValueError(f"评测集为空: {path}")
    return rows


def _docs_to_contexts(docs: List[Dict[str, Any]], top_k: int) -> List[str]:
    contexts: List[str] = []
    for doc in docs[:top_k]:
        if not isinstance(doc, dict):
            continue
        content = (doc.get("content") or "").strip()
        if not content:
            continue
        title = (doc.get("title") or "").strip()
        contexts.append(f"{title}\n{content}" if title else content)
    return contexts


def _run_one_query(question: str, stage: ContextStage, top_k: int) -> Dict[str, Any]:
    state = create_default_state(
        session_id=f"ragas-{uuid.uuid4().hex[:12]}",
        task_id=uuid.uuid4().hex[:12],
        original_query=question,
        is_stream=False,
    )
    result = query_app.invoke(state)

    if stage == "rrf":
        docs = result.get("rrf_chunks") or []
    else:
        docs = result.get("reranked_docs") or result.get("rrf_chunks") or []

    contexts = _docs_to_contexts(docs, top_k=top_k)
    answer = (result.get("answer") or "").strip()
    item_names = result.get("item_names") or []
    short_circuited = bool(answer) and not contexts and not item_names

    return {
        "answer": answer,
        "contexts": contexts,
        "item_names": item_names,
        "rewritten_query": result.get("rewritten_query") or "",
        "short_circuited": short_circuited,
        "num_contexts": len(contexts),
    }


def _build_judge_llm() -> LangchainLLMWrapper:
    api_key = os.getenv("OPENAI_API_KEY", "")
    api_base = os.getenv("OPENAI_API_BASE", "")
    model = os.getenv("RAGAS_JUDGE_MODEL") or os.getenv("LLM_DEFAULT_MODEL") or "qwen-flash"
    if not api_key:
        raise RuntimeError("缺少 OPENAI_API_KEY，无法调用 RAGAS 评判 LLM")

    chat = ChatOpenAI(
        model=model,
        api_key=api_key,
        base_url=api_base or None,
        temperature=0,
    )
    return LangchainLLMWrapper(chat)


def main() -> int:
    parser = argparse.ArgumentParser(description="RAGAS 检索质量评测（本项目 query graph）")
    parser.add_argument(
        "--dataset",
        type=Path,
        default=Path(__file__).with_name("sample_eval.jsonl"),
        help="JSONL 评测集路径",
    )
    parser.add_argument(
        "--stage",
        choices=["reranked", "rrf"],
        default="reranked",
        help="取哪一阶段的检索结果作为 retrieved_contexts",
    )
    parser.add_argument("--top-k", type=int, default=5, help="送入 RAGAS 的上下文条数上限")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).with_name("ragas_report.json"),
        help="结果输出 JSON 路径",
    )
    parser.add_argument(
        "--skip-short-circuit",
        action="store_true",
        help="跳过商品名确认短路（无检索上下文）的样本",
    )
    args = parser.parse_args()

    rows = _load_jsonl(args.dataset)
    logger.info("加载评测集 %s，共 %d 条；stage=%s top_k=%d", args.dataset, len(rows), args.stage, args.top_k)

    eval_records: List[Dict[str, Any]] = []
    run_meta: List[Dict[str, Any]] = []

    for i, row in enumerate(rows, 1):
        qid = row.get("id") or f"row_{i}"
        question = row["question"].strip()
        reference = row["reference"].strip()
        logger.info("[%d/%d] %s | %s", i, len(rows), qid, question[:60])

        try:
            out = _run_one_query(question, stage=args.stage, top_k=args.top_k)
        except Exception as e:
            logger.exception("查询失败 %s: %s", qid, e)
            run_meta.append({"id": qid, "error": str(e)})
            continue

        meta = {
            "id": qid,
            "question": question,
            "item_names": out["item_names"],
            "rewritten_query": out["rewritten_query"],
            "num_contexts": out["num_contexts"],
            "short_circuited": out["short_circuited"],
            "answer_preview": (out["answer"] or "")[:200],
        }
        run_meta.append(meta)

        if args.skip_short_circuit and out["short_circuited"]:
            logger.warning("跳过短路样本 %s（商品名未确认，无检索上下文）", qid)
            continue

        if not out["contexts"]:
            logger.warning("样本 %s 检索上下文为空，仍参与评测（分数可能偏低）", qid)

        eval_records.append(
            {
                "user_input": question,
                "retrieved_contexts": out["contexts"] or [""],
                "reference": reference,
                "response": out["answer"] or "",
            }
        )

    if not eval_records:
        logger.error("没有可评测样本，请检查商品名确认是否通过，或去掉 --skip-short-circuit")
        args.output.write_text(
            json.dumps({"meta": run_meta, "scores": {}, "error": "no_eval_rows"}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return 1

    judge_llm = _build_judge_llm()
    dataset = Dataset.from_list(eval_records)

    logger.info("开始 RAGAS 评估，样本数=%d", len(eval_records))
    result = evaluate(
        dataset=dataset,
        metrics=[context_precision, context_recall],
        llm=judge_llm,
        raise_exceptions=False,
        show_progress=True,
    )

    # EvaluationResult → 可序列化
    try:
        scores = dict(result)
    except Exception:
        scores = {"raw": str(result)}

    report = {
        "dataset": str(args.dataset),
        "stage": args.stage,
        "top_k": args.top_k,
        "judge_model": os.getenv("RAGAS_JUDGE_MODEL") or os.getenv("LLM_DEFAULT_MODEL") or "qwen-flash",
        "num_eval_rows": len(eval_records),
        "scores": scores,
        "per_sample_meta": run_meta,
    }
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    logger.info("评测完成，报告写入 %s", args.output)
    logger.info("scores=%s", scores)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
