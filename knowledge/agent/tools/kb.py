"""知识库相关 Agent tools（能力门面）。"""

from __future__ import annotations

import logging

from agents import RunContextWrapper, function_tool

from knowledge.agent.context import QueryAgentContext
from knowledge.agent.tools.base import (
    execute_node,
    get_node,
    guard_tool,
    run_node,
    tool_result,
)

logger = logging.getLogger(__name__)


@function_tool
def confirm_item(wrapper: RunContextWrapper[QueryAgentContext]) -> str:
    """理解用户问题、识别/对齐产品名。通常作为第一步。

    看返回 next / hint / allowed：
    - clarify → generate_answer
    - chitchat → web_search → prepare_context → generate_answer
    - product → search_kb → …
    """
    return run_node(wrapper.context, get_node("confirm"), tool="confirm_item")


@function_tool
def search_kb(wrapper: RunContextWrapper[QueryAgentContext], query_override: str = "") -> str:
    """知识库混合向量检索（dense+sparse）。

    依赖 confirm_item 得到的 item_names / rewritten_query。
    可选 query_override：临时覆盖 rewritten_query 再检索。
    """
    ctx = wrapper.context
    override = (query_override or "").strip()
    if override:
        ctx.state["rewritten_query"] = override
    return run_node(ctx, get_node("hybrid"), tool="search_kb")


@function_tool
def search_hyde(wrapper: RunContextWrapper[QueryAgentContext], query_override: str = "") -> str:
    """HyDE 假设性文档检索，适合表述模糊、需要语义扩展的问题。

    可选 query_override：临时覆盖 rewritten_query 再检索。
    """
    ctx = wrapper.context
    override = (query_override or "").strip()
    if override:
        ctx.state["rewritten_query"] = override
    return run_node(ctx, get_node("hyde"), tool="search_hyde")


@function_tool
def merge_and_rerank(wrapper: RunContextWrapper[QueryAgentContext]) -> str:
    """融合本地检索结果（RRF）并重排序。应在 search_kb / search_hyde 之后、generate_answer 之前。"""
    ctx = wrapper.context
    blocked = guard_tool(ctx, "merge_and_rerank")
    if blocked is not None:
        return blocked

    try:
        execute_node(ctx, get_node("rrf"))
        execute_node(ctx, get_node("rerank"))
        ctx.record_tool("merge_and_rerank")
        return tool_result(
            ok=True,
            tool="merge_and_rerank",
            ctx=ctx,
            data={"stage": "done", **ctx.summary()},
        )
    except Exception as e:
        logger.exception("merge_and_rerank failed")
        ctx.record_tool("merge_and_rerank")
        return tool_result(
            ok=False,
            tool="merge_and_rerank",
            ctx=ctx,
            data={"stage": "error", **ctx.summary()},
            error=str(e),
        )
