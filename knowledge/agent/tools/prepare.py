"""上下文整理：把检索结果收成 generate_answer 可用的 reranked_docs。

编排胶水放在这里，不放进 generate_answer。
"""

from __future__ import annotations

from agents import RunContextWrapper, function_tool

from knowledge.agent.context import QueryAgentContext
from knowledge.agent.tools.base import guard_tool, tool_result


def _web_docs_to_reranked(web_docs: list) -> list:
    out = []
    for d in web_docs:
        if not isinstance(d, dict):
            continue
        snippet = (d.get("snippet") or "").strip()
        if not snippet:
            continue
        out.append(
            {
                "content": snippet,
                "title": (d.get("title") or "").strip(),
                "url": (d.get("url") or "").strip(),
                "source": "web",
                "score": 1.0,
            }
        )
    return out


@function_tool
def prepare_context(wrapper: RunContextWrapper[QueryAgentContext]) -> str:
    """整理已有检索结果，供 generate_answer 使用。

    - 已有 reranked_docs：确认即可。
    - 仅有 web_search_docs：映射为 reranked_docs；若尚无 query_intent 则标为 chitchat。
    - 知识库路径应先 merge_and_rerank；本工具主要用于联网结果或补齐。
    """
    ctx = wrapper.context
    blocked = guard_tool(ctx, "prepare_context")
    if blocked is not None:
        return blocked

    s = ctx.state
    reranked = s.get("reranked_docs") or []

    if reranked:
        ctx.record_tool("prepare_context")
        return tool_result(
            ok=True,
            tool="prepare_context",
            ctx=ctx,
            data={
                "action": "noop",
                "reranked_docs": len(reranked),
                **ctx.summary(),
            },
        )

    web_docs = s.get("web_search_docs") or []
    if web_docs:
        mapped = _web_docs_to_reranked(web_docs)
        s["reranked_docs"] = mapped
        if not (s.get("query_intent") or "").strip():
            s["query_intent"] = "chitchat"
        ctx.record_tool("prepare_context")
        return tool_result(
            ok=True,
            tool="prepare_context",
            ctx=ctx,
            data={
                "action": "web_to_reranked",
                "mapped": len(mapped),
                **ctx.summary(),
            },
        )

    ctx.record_tool("prepare_context")
    return tool_result(
        ok=True,
        tool="prepare_context",
        ctx=ctx,
        data={
            "action": "empty",
            "note": "no web_search_docs or reranked_docs; generate_answer may rely on clarify text or LLM fallback",
            **ctx.summary(),
        },
    )
