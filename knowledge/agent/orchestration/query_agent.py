"""openai-agents Agent 定义（编排层）。"""

from __future__ import annotations

from agents import Agent

from knowledge.agent.context import QueryAgentContext
from knowledge.agent.orchestration.instructions import QUERY_AGENT_INSTRUCTIONS
from knowledge.agent.runtime.model import build_model, ensure_agent_runtime
from knowledge.agent.tools import QUERY_AGENT_TOOLS


def create_query_agent() -> Agent[QueryAgentContext]:
    ensure_agent_runtime()
    return Agent[QueryAgentContext](
        name="AgentBrainQuery",
        instructions=QUERY_AGENT_INSTRUCTIONS,
        tools=QUERY_AGENT_TOOLS,
        model=build_model(),
    )
