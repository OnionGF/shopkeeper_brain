"""openai-agents 模型与运行时初始化。"""

from __future__ import annotations

import os

from agents import set_default_openai_api, set_tracing_disabled
from agents.models.openai_chatcompletions import OpenAIChatCompletionsModel
from openai import AsyncOpenAI

from knowledge.agent.config import get_agent_config
from knowledge.agent.errors import AgentConfigError

_configured = False


def ensure_agent_runtime() -> None:
    """配置 openai-agents 使用 chat_completions（兼容自建 OpenAI 网关）。"""
    global _configured
    if _configured:
        return
    set_tracing_disabled(True)
    set_default_openai_api("chat_completions")
    cfg = get_agent_config()
    if not cfg.openai_api_key or not cfg.openai_api_base:
        # 再读一次 os.environ，兼容延迟 load_dotenv
        if not os.environ.get("OPENAI_API_KEY") or not os.environ.get("OPENAI_API_BASE"):
            raise AgentConfigError("缺少 OPENAI_API_KEY 或 OPENAI_API_BASE")
    _configured = True


def build_model() -> OpenAIChatCompletionsModel:
    ensure_agent_runtime()
    cfg = get_agent_config()
    api_key = cfg.openai_api_key or os.environ["OPENAI_API_KEY"]
    base_url = cfg.openai_api_base or os.environ["OPENAI_API_BASE"]
    model_name = cfg.model_name
    client = AsyncOpenAI(api_key=api_key, base_url=base_url)
    return OpenAIChatCompletionsModel(model=model_name, openai_client=client)
