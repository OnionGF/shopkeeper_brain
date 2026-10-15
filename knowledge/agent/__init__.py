"""Agent Brain · openai-agents 编排轨（生产级分层）。

能力层仍是 query_processor 节点；本包只负责编排、tool 包装与运行入口。

目录：
  config.py / errors.py
  context/          会话状态
  runtime/          模型 + runner
  orchestration/    instructions + Agent 工厂
  tools/            KB / Web / Answer tools
"""

from knowledge.agent.runtime.runner import run_agent_query

__all__ = ["run_agent_query"]
