"""openai-agents 多 Agent 定义（Router + 专责）。"""

from __future__ import annotations

from agents import Agent, RunContextWrapper, handoff

from knowledge.agent.context import QueryAgentContext
from knowledge.agent.orchestration.instructions import (
    KB_AGENT_INSTRUCTIONS,
    NEWS_AGENT_INSTRUCTIONS,
    ROUTER_INSTRUCTIONS,
    WEB_AGENT_INSTRUCTIONS,
)
from knowledge.agent.runtime.model import build_model, ensure_agent_runtime
from knowledge.agent.tools import KB_TOOLS, NEWS_TOOLS, ROUTER_TOOLS, WEB_TOOLS


def _on_handoff_kb(ctx: RunContextWrapper[QueryAgentContext]) -> None:
    ctx.context.set_active_agent("kb")


def _on_handoff_web(ctx: RunContextWrapper[QueryAgentContext]) -> None:
    ctx.context.set_active_agent("web")


def _on_handoff_news(ctx: RunContextWrapper[QueryAgentContext]) -> None:
    ctx.context.set_active_agent("news")
    # 保证答案模板走 NEWS_ANSWER_PROMPT
    if not (ctx.context.state.get("query_intent") or "").strip():
        ctx.context.state["query_intent"] = "news"


def create_kb_agent() -> Agent[QueryAgentContext]:
    return Agent[QueryAgentContext](
        name="KbAgent",
        handoff_description="产品说明书/用法/参数/故障等知识库问答。",
        instructions=KB_AGENT_INSTRUCTIONS,
        tools=KB_TOOLS,
        model=build_model(),
    )


def create_web_agent() -> Agent[QueryAgentContext]:
    return Agent[QueryAgentContext](
        name="WebAgent",
        handoff_description="闲聊、天气、一般时事问答（不整理成新闻稿）。",
        instructions=WEB_AGENT_INSTRUCTIONS,
        tools=WEB_TOOLS,
        model=build_model(),
    )


def create_news_agent() -> Agent[QueryAgentContext]:
    return Agent[QueryAgentContext](
        name="NewsAgent",
        handoff_description="整理/汇总/摘要新闻、今日要闻、事件盘点。",
        instructions=NEWS_AGENT_INSTRUCTIONS,
        tools=NEWS_TOOLS,
        model=build_model(),
    )


def create_query_agent() -> Agent[QueryAgentContext]:
    """入口 Router：confirm 后 handoff 到 Kb / Web / News。"""
    ensure_agent_runtime()
    model = build_model()

    kb = create_kb_agent()
    web = create_web_agent()
    news = create_news_agent()

    return Agent[QueryAgentContext](
        name="RouterAgent",
        instructions=ROUTER_INSTRUCTIONS,
        tools=ROUTER_TOOLS,
        model=model,
        handoffs=[
            handoff(
                kb,
                tool_name_override="transfer_to_kb_agent",
                tool_description_override="将产品知识库问题交给 KbAgent。",
                on_handoff=_on_handoff_kb,
            ),
            handoff(
                web,
                tool_name_override="transfer_to_web_agent",
                tool_description_override="将闲聊/天气等交给 WebAgent。",
                on_handoff=_on_handoff_web,
            ),
            handoff(
                news,
                tool_name_override="transfer_to_news_agent",
                tool_description_override="将新闻整理/汇总任务交给 NewsAgent。",
                on_handoff=_on_handoff_news,
            ),
        ],
    )
