"""Agent 运行时共享上下文：可变 QueryGraphState + 编排计数。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from knowledge.agent.config import AgentConfig, get_agent_config
from knowledge.agent.orchestration.policy import Decision, decide_next, snapshot_from_context
from knowledge.processor.query_processor.state import QueryGraphState, create_default_state


@dataclass
class QueryAgentContext:
    """编排层上下文：能力层节点读写同一份 state；多 Agent 共享。"""

    state: QueryGraphState = field(default_factory=create_default_state)
    tool_calls: List[str] = field(default_factory=list)
    tool_counts: Dict[str, int] = field(default_factory=dict)
    config: AgentConfig = field(default_factory=get_agent_config)
    active_agent: str = "router"

    def merge(self, updates: Any) -> None:
        """把节点返回值合并进 state（兼容全量 state / 部分 dict）。"""
        if updates is None:
            return
        if isinstance(updates, dict):
            self.state.update(updates)  # type: ignore[arg-type]

    def record_tool(self, tool: str) -> None:
        """记录一次 tool 调用（在真正执行后调用）。"""
        self.tool_calls.append(tool)
        self.tool_counts[tool] = self.tool_counts.get(tool, 0) + 1

    def set_active_agent(self, name: str) -> None:
        self.active_agent = name

    def decision(self) -> Decision:
        return decide_next(snapshot_from_context(self), self.config)

    def summary(self) -> Dict[str, Any]:
        s = self.state
        return {
            "active_agent": self.active_agent,
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
            "tool_call_total": len(self.tool_calls),
            "tool_counts": dict(self.tool_counts),
        }

    def next_hint(self) -> str:
        """兼容 Phase 0：委托 decide_next。"""
        return self.decision().hint
