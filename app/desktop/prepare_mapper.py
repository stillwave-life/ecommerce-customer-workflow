from __future__ import annotations

from typing import Any

from app.models import build_prepared_result


def _first_product_ref(product_context: dict[str, Any]) -> dict[str, str] | None:
    for item in product_context.get("items", []):
        sku = str(item.get("sku", "")).strip()
        if sku:
            return {"type": "sku", "value": sku}
        product_id = str(item.get("product_id", "")).strip()
        if product_id:
            return {"type": "product_id", "value": product_id}
    return None


def _product_entities(product_context: dict[str, Any]) -> list[dict[str, str]]:
    entities: list[dict[str, str]] = []
    for item in product_context.get("items", []):
        sku = str(item.get("sku", "")).strip()
        if sku:
            entities.append({"type": "sku", "value": sku, "source": "desktop_product_context"})
        product_id = str(item.get("product_id", "")).strip()
        if product_id:
            entities.append({"type": "product_id", "value": product_id, "source": "desktop_product_context"})
    return entities


def build_prepared_from_desktop_context(
    desktop_context: dict[str, Any],
    *,
    shop_id: str,
    session_id: str,
) -> dict[str, Any]:
    chat_context = desktop_context.get("chat_context") or {}
    product_context = desktop_context.get("product_context") or {}
    user_message = str(chat_context.get("latest_customer_message", "")).strip()
    product_ref = _first_product_ref(product_context)
    parsed_entities = _product_entities(product_context)
    constraints = None
    reply_strategy = None

    if not user_message:
        constraints = {
            "confirmed": [],
            "candidate": [],
            "conflicted": [],
            "missing": [{"key": "customer_message", "reason": "required_for_reply"}],
            "forbidden_claims": [],
        }
        reply_strategy = "ask_for_clarification"

    return build_prepared_result(
        shop_id=shop_id,
        session_id=session_id,
        source_type="text",
        source_value=user_message,
        product_ref=product_ref,
        user_message=user_message,
        page_context={
            "platform": desktop_context.get("platform", "unknown"),
            "desktop_context": desktop_context,
            "active_customer": desktop_context.get("active_customer", {}),
        },
        parsed_entities=parsed_entities,
        constraints=constraints,
        reply_strategy=reply_strategy,
        session_status="desktop_context_prepared",
    )
