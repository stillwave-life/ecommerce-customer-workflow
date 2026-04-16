from __future__ import annotations

from typing import Any

from app.desktop.context import (
    build_chat_context,
    build_desktop_context,
    build_input_context,
    build_product_context,
    build_user_order_context,
)


def _latest_customer_message(chat_region: list[dict[str, Any]]) -> str:
    for item in chat_region:
        if item.get("message_role") == "customer":
            return str(item.get("text", "")).strip()
    return ""


def _product_items(product_region: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [item.copy() for item in product_region if item.get("title") or item.get("sku")]


def _user_labels(user_order_region: list[dict[str, Any]]) -> list[str]:
    return [str(item.get("label", "")).strip() for item in user_order_region if str(item.get("label", "")).strip()]


def _orders(user_order_region: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{"summary": str(item.get("order_summary", "")).strip()} for item in user_order_region if str(item.get("order_summary", "")).strip()]


def parse_jd_workspace(
    regions: dict[str, list[dict[str, Any]]],
    *,
    active_customer: dict[str, str],
    confidence: float,
) -> dict:
    input_region = regions.get("input_region", [])
    send_button_region = regions.get("send_button_region", [])
    first_input = input_region[0] if input_region else {}

    return build_desktop_context(
        platform="jd_customer_service",
        confidence=confidence,
        active_customer=active_customer,
        chat_context=build_chat_context(
            latest_customer_message=_latest_customer_message(regions.get("chat_region", [])),
            recent_messages=[item.copy() for item in regions.get("chat_region", [])],
            contains_image=any(bool(item.get("contains_image")) for item in regions.get("chat_region", [])),
        ),
        product_context=build_product_context(
            tab_active=bool(regions.get("product_region")),
            items=_product_items(regions.get("product_region", [])),
        ),
        user_order_context=build_user_order_context(
            user_labels=_user_labels(regions.get("user_order_region", [])),
            orders=_orders(regions.get("user_order_region", [])),
            service_forms=[],
        ),
        input_context=build_input_context(
            editable=bool(first_input.get("editable")),
            has_smart_reply=bool(first_input.get("has_smart_reply")),
            send_button_visible=any(bool(item.get("visible")) for item in send_button_region),
            existing_text=str(first_input.get("existing_text", "")),
        ),
    )
