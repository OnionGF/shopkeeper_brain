"""显式编排策略：decide_next（代码路由，不靠长 prompt）。

Phase 1：单 Agent 仍由模型选 tool，但框架用 allowed 白名单约束；
hint / next / reason 写入每次 tool 返回。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Mapping, Sequence, Tuple

from knowledge.agent.config import AgentConfig, get_agent_config

# 与 function_tool / handoff 名称一致
CONFIRM = "confirm_item"
SEARCH_KB = "search_kb"
SEARCH_HYDE = "search_hyde"
WEB_SEARCH = "web_search"
MERGE = "merge_and_rerank"
PREPARE = "prepare_context"
GENERATE = "generate_answer"
TRANSFER_KB = "transfer_to_kb_agent"
TRANSFER_WEB = "transfer_to_web_agent"
TRANSFER_NEWS = "transfer_to_news_agent"


@dataclass(frozen=True)
class PolicySnapshot:
    intent: str
    has_answer: bool
    has_kb: bool
    has_hyde: bool
    has_web: bool
    has_reranked: bool
    tool_counts: Mapping[str, int]
    tool_call_total: int
    active_agent: str = "router"

    def count(self, tool: str) -> int:
        return int(self.tool_counts.get(tool, 0))


@dataclass(frozen=True)
class Decision:
    """下一步决策。"""

    action: str
    allowed: Tuple[str, ...]
    reason: str
    hint: str

    def allows(self, tool: str) -> bool:
        return tool in self.allowed

    def as_dict(self) -> Dict[str, object]:
        return {
            "next": self.action,
            "allowed": list(self.allowed),
            "reason": self.reason,
            "hint": self.hint,
        }


def _dec(action: str, allowed: Sequence[str], reason: str, hint: str) -> Decision:
    uniq = tuple(dict.fromkeys(allowed))  # 保序去重
    if action not in uniq:
        uniq = (action,) + uniq
    return Decision(action=action, allowed=uniq, reason=reason, hint=hint)


def decide_next(snap: PolicySnapshot, cfg: AgentConfig | None = None) -> Decision:
    """根据快照决定下一步（纯函数，可单测）。"""
    cfg = cfg or get_agent_config()
    intent = (snap.intent or "").strip()
    agent = (snap.active_agent or "router").strip() or "router"

    # --- Router：只 confirm / 澄清回答 / handoff ---
    if agent == "router":
        if snap.count(CONFIRM) == 0 and not intent and not snap.has_answer:
            return _dec(
                CONFIRM,
                (CONFIRM,),
                "need_confirm",
                "start: call confirm_item",
            )
        if snap.has_answer and not snap.has_kb and not snap.has_web and not snap.has_reranked:
            return _dec(
                GENERATE,
                (GENERATE,),
                "clarify",
                "clarify_ready: call generate_answer",
            )
        if intent == "product":
            return _dec(
                TRANSFER_KB,
                (TRANSFER_KB,),
                "route_product",
                "route: transfer_to_kb_agent",
            )
        if intent == "news":
            return _dec(
                TRANSFER_NEWS,
                (TRANSFER_NEWS,),
                "route_news",
                "route: transfer_to_news_agent",
            )
        if intent == "chitchat":
            return _dec(
                TRANSFER_WEB,
                (TRANSFER_WEB,),
                "route_chitchat",
                "route: transfer_to_web_agent",
            )
        # confirm 后仍无 intent：再 confirm 一次或按产品兜底交接
        if snap.count(CONFIRM) > 0:
            return _dec(
                TRANSFER_KB,
                (TRANSFER_KB, CONFIRM),
                "route_fallback_kb",
                "route: transfer_to_kb_agent (or re-confirm_item)",
            )
        return _dec(
            CONFIRM,
            (CONFIRM,),
            "need_confirm",
            "start: call confirm_item",
        )

    # --- 预算耗尽：收口到可交付 ---
    if snap.tool_call_total >= cfg.max_tool_calls:
        if snap.has_web and not snap.has_reranked and not snap.has_answer:
            return _dec(
                PREPARE,
                (PREPARE, GENERATE),
                "budget_exhausted",
                "budget: call prepare_context then generate_answer",
            )
        return _dec(
            GENERATE,
            (GENERATE,),
            "budget_exhausted",
            "budget: call generate_answer now",
        )

    # --- 已可交付 ---
    if snap.has_reranked or (snap.has_answer and snap.count(GENERATE) == 0):
        # 澄清文案已在 confirm 写入 answer，或已有 reranked
        if snap.has_reranked or (
            snap.has_answer and not snap.has_kb and not snap.has_web and not snap.has_hyde
        ):
            return _dec(
                GENERATE,
                (GENERATE,),
                "ready_to_answer",
                "ready: call generate_answer",
            )

    if snap.has_answer and not snap.has_kb and not snap.has_web and not snap.has_reranked:
        return _dec(
            GENERATE,
            (GENERATE,),
            "clarify",
            "clarify_ready: call generate_answer",
        )

    # --- 闲聊 / 新闻整理轨（均走联网，不进知识库）---
    if intent in ("chitchat", "news") or agent in ("web", "news"):
        if agent == "news" and not intent:
            intent = "news"
        if agent == "web" and not intent:
            intent = "chitchat"
    if intent in ("chitchat", "news"):
        tag = intent
        if not snap.has_web:
            return _dec(
                WEB_SEARCH,
                (WEB_SEARCH,),
                f"{tag}_need_web",
                f"{tag}: call web_search → prepare_context → generate_answer",
            )
        if not snap.has_reranked:
            return _dec(
                PREPARE,
                (PREPARE,),
                f"{tag}_need_prepare",
                f"{tag}: call prepare_context → generate_answer",
            )
        return _dec(
            GENERATE,
            (GENERATE,),
            f"{tag}_ready",
            "ready: call generate_answer",
        )

    # --- 产品 / 默认：知识库优先 ---
    # 已有 KB/HyDE 命中 → 融合
    if (snap.has_kb or snap.has_hyde) and not snap.has_reranked:
        return _dec(
            MERGE,
            (MERGE,),
            "kb_hits",
            "kb_hits: call merge_and_rerank → generate_answer",
        )

    # 仅有 web（产品问补网或回退）→ prepare
    if snap.has_web and not snap.has_reranked and not snap.has_kb and not snap.has_hyde:
        return _dec(
            PREPARE,
            (PREPARE, GENERATE),
            "web_only",
            "web_hits: call prepare_context → generate_answer",
        )

    # KB 已搜但空、还没 HyDE → 优先 HyDE
    if (
        snap.count(SEARCH_KB) > 0
        and not snap.has_kb
        and not snap.has_hyde
        and not snap.has_web
        and cfg.allow_hyde_retry
        and snap.count(SEARCH_HYDE) == 0
    ):
        return _dec(
            SEARCH_HYDE,
            (SEARCH_HYDE, SEARCH_KB),
            "kb_empty_try_hyde",
            "kb_empty: call search_hyde then merge_and_rerank (or retry search_kb)",
        )

    # KB+HyDE 皆空（或已尝试检索）→ web 回退一次
    if (
        not snap.has_kb
        and not snap.has_hyde
        and not snap.has_web
        and cfg.allow_web_fallback_on_empty_kb
        and snap.count(SEARCH_KB) + snap.count(SEARCH_HYDE) > 0
        and snap.count(WEB_SEARCH) == 0
    ):
        return _dec(
            WEB_SEARCH,
            (WEB_SEARCH, GENERATE),
            "kb_empty_web_fallback",
            "kb_empty: call web_search → prepare_context → generate_answer (or generate_answer)",
        )

    # 尚未检索：先 KB，可选 HyDE
    if not snap.has_kb and not snap.has_hyde and not snap.has_web:
        allowed = [SEARCH_KB]
        if cfg.allow_hyde_retry:
            allowed.append(SEARCH_HYDE)
        return _dec(
            SEARCH_KB,
            allowed,
            "need_kb",
            "product: call search_kb"
            + (" (optional search_hyde)" if cfg.allow_hyde_retry else "")
            + "; then merge_and_rerank → generate_answer",
        )

    # 已 merge 完
    if snap.has_reranked:
        return _dec(
            GENERATE,
            (GENERATE,),
            "merged_ready",
            "ready: call generate_answer",
        )

    # 兜底：强制生成，避免空转
    return _dec(
        GENERATE,
        (GENERATE, PREPARE),
        "fallback_generate",
        "fallback: call generate_answer (prepare_context if web docs pending)",
    )


def snapshot_from_context(ctx: object) -> PolicySnapshot:
    """从 QueryAgentContext 提取快照（避免 policy 依赖具体类细节过多）。"""
    state = getattr(ctx, "state", {}) or {}
    counts = getattr(ctx, "tool_counts", {}) or {}
    calls = getattr(ctx, "tool_calls", []) or []
    return PolicySnapshot(
        intent=(state.get("query_intent") or "").strip(),
        has_answer=bool(state.get("answer")),
        has_kb=bool(state.get("embedding_chunks") or []),
        has_hyde=bool(state.get("hyde_embedding_chunks") or []),
        has_web=bool(state.get("web_search_docs") or []),
        has_reranked=bool(state.get("reranked_docs") or []),
        tool_counts=dict(counts),
        tool_call_total=len(calls),
        active_agent=(getattr(ctx, "active_agent", None) or "router"),
    )
