"""Agent 轨运行配置（集中读环境变量）。"""

from __future__ import annotations

import os
from dataclasses import dataclass


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class AgentConfig:
    """openai-agents 编排层配置。"""

    max_turns: int = 12
    max_tool_calls: int = 10
    allow_hyde_retry: bool = True
    allow_web_fallback_on_empty_kb: bool = True
    model_name: str = "gpt-4o-mini"
    openai_api_key: str = ""
    openai_api_base: str = ""
    fallback_answer: str = "本次未能生成有效回答，请换个问法或指定产品型号后再试。"

    @classmethod
    def from_env(cls) -> "AgentConfig":
        return cls(
            max_turns=int(os.getenv("AGENT_MAX_TURNS", "12")),
            max_tool_calls=int(os.getenv("AGENT_MAX_TOOL_CALLS", "10")),
            allow_hyde_retry=_env_bool("AGENT_ALLOW_HYDE_RETRY", True),
            allow_web_fallback_on_empty_kb=_env_bool("AGENT_ALLOW_WEB_FALLBACK", True),
            model_name=os.getenv("LLM_DEFAULT_MODEL") or "gpt-4o-mini",
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            openai_api_base=os.getenv("OPENAI_API_BASE", ""),
            fallback_answer=os.getenv(
                "AGENT_FALLBACK_ANSWER",
                "本次未能生成有效回答，请换个问法或指定产品型号后再试。",
            ),
        )


def get_agent_config() -> AgentConfig:
    return AgentConfig.from_env()
