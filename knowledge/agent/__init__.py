"""Agent Brain · openai-agents 编排轨（生产级分层）。

能力层仍是 query_processor 节点；本包只负责编排、tool 包装与运行入口。

目录：
  config.py / errors.py
  context/          会话状态 + next_hint
  runtime/          模型 + runner
  orchestration/    Router+专责 Agent、decide_next、instructions
  tools/            按 Router/KB/Web/News 分组的能力门面
"""

from knowledge.agent.runtime.runner import run_agent_query

__all__ = ["run_agent_query"]
