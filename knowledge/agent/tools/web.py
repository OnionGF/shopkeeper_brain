"""联网（MCP）相关 Agent tools。"""

from __future__ import annotations

from agents import RunContextWrapper, function_tool

from knowledge.agent.context import QueryAgentContext
from knowledge.agent.tools.base import get_node, run_node


@function_tool
def web_search(wrapper: RunContextWrapper[QueryAgentContext], query_override: str = "") -> str:
    """联网搜索（MCP / bailian_web_search）。

    闲聊、天气、时事，或产品问答需要时效补充时调用。
    可选 query_override：覆盖 rewritten_query / 检索问法。
    成功后请调用 prepare_context，再 generate_answer。
    """
    ctx = wrapper.context
    override = (query_override or "").strip()
    if override:
        # web 节点主要读 rewritten_query；无则部分实现会回退 original_query
        ctx.state["rewritten_query"] = override
    return run_node(ctx, get_node("web"), tool="web_search")
