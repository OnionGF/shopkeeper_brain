"""Agent 运行时共享上下文：可变 QueryGraphState。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict

from knowledge.processor.query_processor.state import QueryGraphState, create_default_state


@dataclass
class QueryAgentContext:
    """编排层上下文：能力层节点读写同一份 state。"""

    state: QueryGraphState = field(default_factory=create_default_state)

    def merge(self, updates: Any) -> None:
        """把节点返回值合并进 state（兼容全量 state / 部分 dict）。"""
        if updates is None:
            return
        if isinstance(updates, dict):
            self.state.update(updates)  # type: ignore[arg-type]

    def summary(self) -> Dict[str, Any]:
        s = self.state
        return {
            "item_names": s.get("item_names") or [],
            "rewritten_query": s.get("rewritten_query") or "",
            "query_intent": s.get("query_intent") or "",
            "has_answer": bool(s.get("answer")),
            "answer_preview": (s.get("answer") or "")[:200],
            "embedding_chunks": len(s.get("embedding_chunks") or []),
            "hyde_chunks": len(s.get("hyde_embedding_chunks") or []),
            "web_docs": len(s.get("web_search_docs") or []),
            "rrf_chunks": len(s.get("rrf_chunks") or []),
            "reranked_docs": len(s.get("reranked_docs") or []),
        }
