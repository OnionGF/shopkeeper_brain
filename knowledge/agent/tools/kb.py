"""知识库相关 Agent tools。"""

from __future__ import annotations

import json

from agents import RunContextWrapper, function_tool

from knowledge.agent.context import QueryAgentContext
from knowledge.agent.tools.base import get_node, run_node, safe_json_loads


@function_tool
def confirm_item(wrapper: RunContextWrapper[QueryAgentContext]) -> str:
    """理解用户问题、识别/对齐产品名。
    通常应作为第一步调用。
    - has_answer=true：需澄清商品，接着 generate_answer 结束。
    - query_intent=chitchat：闲聊/无关问题，接着 web_search → generate_answer。
    - query_intent=product：继续知识库检索流程。
    """
    return run_node(wrapper.context, get_node("confirm"))


@function_tool
def search_kb(wrapper: RunContextWrapper[QueryAgentContext]) -> str:
    """知识库混合向量检索（dense+sparse），依赖 confirm_item 得到的 item_names / rewritten_query。"""
    return run_node(wrapper.context, get_node("hybrid"))


@function_tool
def search_hyde(wrapper: RunContextWrapper[QueryAgentContext]) -> str:
    """HyDE 假设性文档检索，适合表述模糊、需要语义扩展的问题。"""
    return run_node(wrapper.context, get_node("hyde"))


@function_tool
def merge_and_rerank(wrapper: RunContextWrapper[QueryAgentContext]) -> str:
    """融合本地检索结果（RRF）并对结果重排序。应在检索类工具之后、生成答案之前调用。"""
    out1 = run_node(wrapper.context, get_node("rrf"))
    out2 = run_node(wrapper.context, get_node("rerank"))
    return json.dumps(
        {
            "ok": True,
            "rrf": safe_json_loads(out1) or {"raw": out1},
            "rerank": safe_json_loads(out2) or {"raw": out2},
        },
        ensure_ascii=False,
    )
