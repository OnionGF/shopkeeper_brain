"""Agent tools 聚合导出（按专责 Agent 分组）。"""

from knowledge.agent.tools.answer import generate_answer
from knowledge.agent.tools.kb import confirm_item, merge_and_rerank, search_hyde, search_kb
from knowledge.agent.tools.prepare import prepare_context
from knowledge.agent.tools.web import web_search

# Router：确认意图 + 澄清直接回答
ROUTER_TOOLS = [
    confirm_item,
    generate_answer,
]

# 知识库专责
KB_TOOLS = [
    search_kb,
    search_hyde,
    web_search,
    merge_and_rerank,
    prepare_context,
    generate_answer,
]

# 闲聊联网专责
WEB_TOOLS = [
    web_search,
    prepare_context,
    generate_answer,
]

# 新闻整理专责（复用联网能力，答案模板由 query_intent=news 区分）
NEWS_TOOLS = [
    web_search,
    prepare_context,
    generate_answer,
]

# 兼容：完整工具集（单 Agent / 调试）
QUERY_AGENT_TOOLS = [
    confirm_item,
    search_kb,
    search_hyde,
    web_search,
    merge_and_rerank,
    prepare_context,
    generate_answer,
]

__all__ = [
    "QUERY_AGENT_TOOLS",
    "ROUTER_TOOLS",
    "KB_TOOLS",
    "WEB_TOOLS",
    "NEWS_TOOLS",
    "confirm_item",
    "search_kb",
    "search_hyde",
    "web_search",
    "merge_and_rerank",
    "prepare_context",
    "generate_answer",
]
