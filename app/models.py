from __future__ import annotations

from typing import Any


EMPTY_KNOWLEDGE_HITS = {"catalog": [], "faq": [], "rules": []}
EMPTY_CONSTRAINTS = {
    "confirmed": [],
    "candidate": [],
    "conflicted": [],
    "missing": [],
    "forbidden_claims": [],
}


def normalize_string(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized or None


def build_product_ref(ref_type: str | None = None, ref_value: str | None = None) -> dict[str, str] | None:
    normalized_type = normalize_string(ref_type)
    normalized_value = normalize_string(ref_value)
    if not normalized_type or not normalized_value:
        return None
    return {"type": normalized_type.lower(), "value": normalized_value}


def build_prepared_result(
    *,
    shop_id: str,
    session_id: str,
    source_type: str,
    source_value: str,
    user_message: str,
    product_ref: dict[str, str] | None = None,
    page_context: dict[str, Any] | None = None,
    parsed_entities: list[dict[str, Any]] | None = None,
    knowledge_hits: dict[str, list[dict[str, Any]]] | None = None,
    memory_hits: list[dict[str, Any]] | None = None,
    constraints: dict[str, list[dict[str, Any]]] | None = None,
    reply_strategy: str | None = None,
    session_status: str | None = None,
) -> dict[str, Any]:
    return {
        "shop_id": shop_id,
        "session_id": session_id,
        "source_type": source_type,
        "source_value": source_value,
        "product_ref": product_ref,
        "user_message": user_message,
        "page_context": page_context or {},
        "parsed_entities": parsed_entities or [],
        "knowledge_hits": knowledge_hits or {key: value[:] for key, value in EMPTY_KNOWLEDGE_HITS.items()},
        "memory_hits": memory_hits or [],
        "constraints": constraints or {key: value[:] for key, value in EMPTY_CONSTRAINTS.items()},
        "reply_strategy": reply_strategy,
        "session_status": session_status,
    }


def build_error_response(message: str, **extra: Any) -> dict[str, Any]:
    payload = {"ok": False, "error": message}
    payload.update({key: value for key, value in extra.items() if value is not None})
    return payload


def build_success_response(**extra: Any) -> dict[str, Any]:
    payload = {"ok": True}
    payload.update(extra)
    return payload


def build_reply_response(
    reply_draft: str,
    reply_reasoning_summary: str,
    facts_used: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "ok": True,
        "reply_draft": reply_draft,
        "reply_reasoning_summary": reply_reasoning_summary,
        "facts_used": facts_used or [],
    }
