"""Agent 轨运行配置（集中读环境变量）。"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class AgentConfig:
    """openai-agents 编排层配置。"""

    max_turns: int = 12
    model_name: str = "gpt-4o-mini"
    openai_api_key: str = ""
    openai_api_base: str = ""
    fallback_answer: str = "本次未能生成有效回答，请换个问法或指定产品型号后再试。"

    @classmethod
    def from_env(cls) -> "AgentConfig":
        return cls(
            max_turns=int(os.getenv("AGENT_MAX_TURNS", "12")),
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
