"""Tool 公共：节点单例懒加载 + 安全执行包装。"""

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


def run_node(ctx: QueryAgentContext, node: BaseNode) -> str:
    """执行节点并合并 state，返回给 Agent 的短摘要 JSON（异常不打穿循环）。"""
    try:
        result = node(ctx.state)
        ctx.merge(result)
        payload: dict[str, Any] = {"ok": True, "node": node.name, **ctx.summary()}
        return json.dumps(payload, ensure_ascii=False)
    except Exception as e:
        logger.exception("tool node %s failed", node.name)
        return json.dumps(
            {"ok": False, "node": node.name, "error": str(e), **ctx.summary()},
            ensure_ascii=False,
        )


def safe_json_loads(raw: str) -> Optional[dict]:
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        return None
