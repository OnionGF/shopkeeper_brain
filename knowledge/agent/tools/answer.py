"""答案生成 Agent tool（纯能力门面，不含编排胶水）。"""

from __future__ import annotations

from agents import RunContextWrapper, function_tool

from knowledge.agent.context import QueryAgentContext
from knowledge.agent.tools.base import get_node, run_node


@function_tool
def generate_answer(wrapper: RunContextWrapper[QueryAgentContext]) -> str:
    """根据当前 state 生成最终回答（支持流式 SSE）。流程末尾必须调用。

    调用前请确保：
    - 澄清：confirm_item 已写入 answer；或
    - 知识库：已 merge_and_rerank；或
    - 联网：已 prepare_context（把 web_search_docs 收成 reranked_docs）。
    """
    return run_node(wrapper.context, get_node("answer"), tool="generate_answer")
