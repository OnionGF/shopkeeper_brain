"""联网（MCP）相关 Agent tools。"""

from __future__ import annotations

from agents import RunContextWrapper, function_tool

from knowledge.agent.context import QueryAgentContext
from knowledge.agent.tools.base import get_node, run_node


@function_tool
def web_search(wrapper: RunContextWrapper[QueryAgentContext]) -> str:
    """联网搜索（MCP / bailian_web_search）。
    闲聊、天气、时事，或产品问答需要时效补充时调用。不要求必须有 item_names。
    """
    return run_node(wrapper.context, get_node("web"))
