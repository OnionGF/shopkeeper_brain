"""Agent 查询运行入口（供 API background task 调用）。"""

from __future__ import annotations

import logging
import os

from agents import Runner
from dotenv import load_dotenv

from knowledge.agent.config import get_agent_config
from knowledge.agent.context import QueryAgentContext
from knowledge.agent.errors import AgentQueryError
from knowledge.agent.orchestration.query_agent import create_query_agent
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
        )
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
        if not answer:
            answer = cfg.fallback_answer
            ctx.state["answer"] = answer

        update_task_status(task_id=task_id, status_name=TASK_STATUS_COMPLETED)
        _finalize_stream(task_id, is_stream, answer=answer)
    except Exception as e:
        logger.error("Agent 查询失败: %s", e, exc_info=True)
        update_task_status(task_id=task_id, status_name=TASK_STATUS_FAILED)
        _finalize_stream(task_id, is_stream, error=str(e))
        raise AgentQueryError(str(e)) from e
