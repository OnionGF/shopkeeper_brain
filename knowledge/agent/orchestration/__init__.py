"""Agent 编排：策略为稳定导出；Agent 工厂请从 query_agent 导入（避免与 context 循环依赖）。"""

from knowledge.agent.orchestration.policy import Decision, decide_next, snapshot_from_context

__all__ = [
    "decide_next",
    "Decision",
    "snapshot_from_context",
]


def __getattr__(name: str):
    if name == "create_query_agent":
        from knowledge.agent.orchestration.query_agent import create_query_agent

        return create_query_agent
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
