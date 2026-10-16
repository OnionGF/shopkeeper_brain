"""Tool 公共：节点单例懒加载 + 统一 JSON 契约 + 策略门禁。"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional

from knowledge.agent.context import QueryAgentContext
from knowledge.processor.query_processor.base import BaseNode
from knowledge.processor.query_processor.nodes.answer_output_node import AnswerOutputNode
from knowledge.processor.query_processor.nodes.hybrid_vector_search_node import HybridVectorSearchNode
from knowledge.processor.query_processor.nodes.hyde_vector_search_node import HydeVectorSearchNode
from knowledge.processor.query_processor.nodes.item_name_confirmed_node import ItemNameConfirmedNode
from knowledge.processor.query_processor.nodes.rerank_node import RerankerNode
from knowledge.processor.query_processor.nodes.rrf_merge_node import RrfMergeNode
from knowledge.processor.query_processor.nodes.web_mcp_search_node import WebMcpSearchNode

logger = logging.getLogger(__name__)

_nodes: Dict[str, BaseNode] = {}


def get_node(name: str) -> BaseNode:
    """懒加载节点单例，避免 import 期强依赖外部服务。"""
    if name not in _nodes:
        factories = {
            "confirm": ItemNameConfirmedNode,
            "hybrid": HybridVectorSearchNode,
            "hyde": HydeVectorSearchNode,
            "web": WebMcpSearchNode,
            "rrf": RrfMergeNode,
            "rerank": RerankerNode,
            "answer": AnswerOutputNode,
        }
        factory = factories.get(name)
        if factory is None:
            raise KeyError(f"unknown agent tool node: {name}")
        _nodes[name] = factory()
    return _nodes[name]


def tool_result(
    *,
    ok: bool,
    tool: str,
    ctx: QueryAgentContext,
    data: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None,
) -> str:
    """统一 Tool 返回：ok / tool / data / hint / next / allowed / reason / error。"""
    decision = ctx.decision()
    payload: Dict[str, Any] = {
        "ok": ok,
        "tool": tool,
        "data": data if data is not None else {},
        "hint": decision.hint,
        "next": decision.action,
        "allowed": list(decision.allowed),
        "reason": decision.reason,
        "error": error,
    }
    return json.dumps(payload, ensure_ascii=False)


def guard_tool(ctx: QueryAgentContext, tool: str) -> Optional[str]:
    """策略门禁：不在 allowed 内则拒绝执行节点，返回错误 JSON。"""
    decision = ctx.decision()
    if decision.allows(tool):
        return None
    return tool_result(
        ok=False,
        tool=tool,
        ctx=ctx,
        data={"blocked": True, "attempted": tool, **ctx.summary()},
        error=f"policy blocked '{tool}'; next={decision.action}; allowed={list(decision.allowed)}",
    )


def execute_node(ctx: QueryAgentContext, node: BaseNode) -> None:
    """执行节点并 merge（无门禁、不记 tool、不组 JSON）。供复合 tool 内部使用。"""
    result = node(ctx.state)
    ctx.merge(result)


def run_node(ctx: QueryAgentContext, node: BaseNode, *, tool: str) -> str:
    """策略门禁 → 执行节点 → 记录调用 → 返回统一契约 JSON。"""
    blocked = guard_tool(ctx, tool)
    if blocked is not None:
        logger.info("policy blocked tool=%s decision=%s", tool, ctx.decision().as_dict())
        return blocked

    try:
        execute_node(ctx, node)
        ctx.record_tool(tool)
        return tool_result(
            ok=True,
            tool=tool,
            ctx=ctx,
            data={"node": node.name, **ctx.summary()},
        )
    except Exception as e:
        logger.exception("tool node %s failed", node.name)
        ctx.record_tool(tool)
        return tool_result(
            ok=False,
            tool=tool,
            ctx=ctx,
            data={"node": node.name, **ctx.summary()},
            error=str(e),
        )


def safe_json_loads(raw: str) -> Optional[dict]:
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        return None
