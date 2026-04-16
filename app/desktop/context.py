from __future__ import annotations

from typing import Any


def _copy_list(value: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    return [item.copy() for item in value or []]


def build_chat_context(
    *,
    latest_customer_message: str = "",
    recent_messages: list[dict[str, Any]] | None = None,
    contains_image: bool = False,
) -> dict[str, Any]:
    return {
        "latest_customer_message": latest_customer_message,
        "recent_messages": _copy_list(recent_messages),
        "contains_image": contains_image,
    }


def build_product_context(
    *,
    tab_active: bool = False,
    items: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "tab_active": tab_active,
        "items": _copy_list(items),
    }


def build_user_order_context(
    *,
    user_labels: list[str] | None = None,
    orders: list[dict[str, Any]] | None = None,
    service_forms: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "user_labels": list(user_labels or []),
        "orders": _copy_list(orders),
        "service_forms": _copy_list(service_forms),
    }


def build_input_context(
    *,
    editable: bool = False,
    has_smart_reply: bool = False,
    send_button_visible: bool = False,
    existing_text: str = "",
) -> dict[str, Any]:
    return {
        "editable": editable,
        "has_smart_reply": has_smart_reply,
        "send_button_visible": send_button_visible,
        "existing_text": existing_text,
    }


def build_desktop_context(
    *,
    platform: str = "unknown",
    confidence: float = 0.0,
    active_customer: dict[str, str] | None = None,
    chat_context: dict[str, Any] | None = None,
    product_context: dict[str, Any] | None = None,
    user_order_context: dict[str, Any] | None = None,
    input_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "platform": platform,
        "confidence": confidence,
        "active_customer": (active_customer or {"id": "", "name": ""}).copy(),
        "chat_context": chat_context or build_chat_context(),
        "product_context": product_context or build_product_context(),
        "user_order_context": user_order_context or build_user_order_context(),
        "input_context": input_context or build_input_context(),
    }
