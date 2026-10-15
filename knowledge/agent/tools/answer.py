"""答案生成 Agent tool。"""

from __future__ import annotations

from agents import RunContextWrapper, function_tool

from knowledge.agent.context import QueryAgentContext
from knowledge.agent.tools.base import get_node, run_node


@function_tool
def generate_answer(wrapper: RunContextWrapper[QueryAgentContext]) -> str:
    """根据当前 state 生成最终回答（支持流式 SSE）。流程末尾必须调用。
    若 confirm_item 已写入澄清文案会直接推送；闲聊会结合 web_search 结果由外部 LLM 作答。
    """
    ctx = wrapper.context
    # 若跳过 merge_and_rerank（常见于闲聊只调 web_search），把联网结果灌进 reranked_docs
    if not (ctx.state.get("reranked_docs") or []):
        web_docs = ctx.state.get("web_search_docs") or []
        if web_docs:
            ctx.state["reranked_docs"] = [
                {
                    "content": (d.get("snippet") or "").strip(),
                    "title": (d.get("title") or "").strip(),
                    "url": (d.get("url") or "").strip(),
                    "source": "web",
                    "score": 1.0,
                }
                for d in web_docs
                if isinstance(d, dict) and (d.get("snippet") or "").strip()
            ]
            # 无 confirm 时也按闲聊提示词作答，避免 ANSWER_PROMPT 拒答
            if not ctx.state.get("query_intent"):
                ctx.state["query_intent"] = "chitchat"
    return run_node(ctx, get_node("answer"))
