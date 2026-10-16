"""Agent 查询运行入口（供 API background task 调用）。"""

from __future__ import annotations

import logging
import os

from agents import Runner
from dotenv import load_dotenv

from knowledge.agent.config import get_agent_config
from knowledge.agent.context import QueryAgentContext
from knowledge.agent.errors import AgentQueryError
from knowledge.agent.orchestration.policy import GENERATE, PREPARE, decide_next, snapshot_from_context
from knowledge.agent.orchestration.query_agent import create_query_agent
from knowledge.agent.tools.base import execute_node, get_node
from knowledge.agent.tools.prepare import _web_docs_to_reranked
from knowledge.core.paths import KNOWLEDGE_ROOT
from knowledge.processor.query_processor.state import create_default_state
from knowledge.utils.sse_util import SSEEvent, push_sse_event
from knowledge.utils.task_util import (
    TASK_STATUS_COMPLETED,
    TASK_STATUS_FAILED,
    TASK_STATUS_PROCESSING,
    set_task_result,
    update_task_status,
)

load_dotenv(os.path.join(KNOWLEDGE_ROOT, ".env"))
logger = logging.getLogger(__name__)


def _finalize_stream(task_id: str, is_stream: bool, *, answer: str = "", error: str = "") -> None:
    """保证前端一定收到 final，避免气泡卡在 streaming。"""
    if not is_stream:
        if error:
            set_task_result(task_id=task_id, key="error", value=error)
        if answer:
            set_task_result(task_id=task_id, key="answer", value=answer)
        return
    data: dict = {}
    if error:
        data["error"] = error
    if answer:
        data["answer"] = answer
    push_sse_event(task_id=task_id, event=SSEEvent.FINAL, data=data)


def _ensure_answer(ctx: QueryAgentContext) -> None:
    """Agent 循环结束后的安全网：按策略补 prepare / generate，避免无答。"""
    if (ctx.state.get("answer") or "").strip():
        return

    decision = decide_next(snapshot_from_context(ctx), ctx.config)
    logger.info("post-run ensure_answer decision=%s", decision.as_dict())

    if decision.action == PREPARE or (
        PREPARE in decision.allowed
        and (ctx.state.get("web_search_docs") or [])
        and not (ctx.state.get("reranked_docs") or [])
    ):
        web_docs = ctx.state.get("web_search_docs") or []
        if web_docs and not (ctx.state.get("reranked_docs") or []):
            ctx.state["reranked_docs"] = _web_docs_to_reranked(web_docs)
            if not (ctx.state.get("query_intent") or "").strip():
                ctx.state["query_intent"] = "chitchat"
            ctx.record_tool(PREPARE)

    # 只要还没答案就生成（含澄清文案已在 state.answer 的情况上面已 return）
    try:
        execute_node(ctx, get_node("answer"))
        ctx.record_tool(GENERATE)
    except Exception:
        logger.exception("post-run generate_answer failed")


def run_agent_query(session_id: str, task_id: str, query: str, is_stream: bool) -> None:
    """运行 openai-agents 编排；节点内部复用 SSE progress/delta/final。"""
    cfg = get_agent_config()
    update_task_status(task_id=task_id, status_name=TASK_STATUS_PROCESSING)

    ctx = QueryAgentContext(
        state=create_default_state(
            session_id=session_id,
            task_id=task_id,
            original_query=query,
            is_stream=is_stream,
        ),
        config=cfg,
    )

    try:
        agent = create_query_agent()
        result = Runner.run_sync(
            agent,
            input=query,
            context=ctx,
            max_turns=cfg.max_turns,
        )
        answer = (ctx.state.get("answer") or "").strip()
        if not answer:
            final_output = getattr(result, "final_output", None)
            if isinstance(final_output, str) and final_output.strip():
                answer = final_output.strip()
                ctx.state["answer"] = answer

        if not (ctx.state.get("answer") or "").strip():
            _ensure_answer(ctx)

        answer = (ctx.state.get("answer") or "").strip()
        if not answer:
            answer = cfg.fallback_answer
            ctx.state["answer"] = answer

        logger.info(
            "agent done active=%s tools=%s counts=%s",
            ctx.active_agent,
            ctx.tool_calls,
            ctx.tool_counts,
        )
        update_task_status(task_id=task_id, status_name=TASK_STATUS_COMPLETED)
        _finalize_stream(task_id, is_stream, answer=answer)
    except Exception as e:
        logger.error("Agent 查询失败: %s", e, exc_info=True)
        update_task_status(task_id=task_id, status_name=TASK_STATUS_FAILED)
        _finalize_stream(task_id, is_stream, error=str(e))
        raise AgentQueryError(str(e)) from e
