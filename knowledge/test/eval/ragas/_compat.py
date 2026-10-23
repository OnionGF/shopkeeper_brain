"""兼容 shim：新版 langchain-community 移除了 vertexai 路径，RAGAS 0.2.x 仍会 import。"""

from __future__ import annotations

import sys
from types import ModuleType


def ensure_ragas_imports() -> None:
    key = "langchain_community.chat_models.vertexai"
    if key in sys.modules:
        return
    mod = ModuleType(key)

    class ChatVertexAI:  # noqa: N801
        """占位类，仅满足 RAGAS import，不会真实调用。"""

    mod.ChatVertexAI = ChatVertexAI
    sys.modules[key] = mod
