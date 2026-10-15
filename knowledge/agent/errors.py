"""Agent 轨错误类型。"""

from __future__ import annotations


class AgentError(Exception):
    """Agent 轨基础异常。"""


class AgentConfigError(AgentError):
    """缺少或非法的运行时配置。"""


class AgentQueryError(AgentError):
    """单次查询执行失败。"""
