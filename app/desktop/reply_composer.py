from __future__ import annotations

from typing import Any

from app.desktop.prepare_mapper import build_prepared_from_desktop_context
from app.reply.reply_builder import build_reply_draft


def _can_fill_input(desktop_context: dict[str, Any]) -> bool:
    input_context = desktop_context.get("input_context") or {}
    return bool(input_context.get("editable")) and bool(input_context.get("send_button_visible"))


def _ui_context_summary(desktop_context: dict[str, Any]) -> dict[str, Any]:
    return {
        "left_conversation_summary": desktop_context.get("left_conversation_summary", {}),
        "chat_region_summary": desktop_context.get("chat_region_summary", {}),
        "right_panel_summary": desktop_context.get("right_panel_summary", {}),
    }


def compose_desktop_reply(
    desktop_context: dict[str, Any],
    *,
    shop_id: str,
    session_id: str,
    latest_customer_message_override: str | None = None,
) -> dict[str, Any]:
    prepared = build_prepared_from_desktop_context(
        desktop_context,
        shop_id=shop_id,
        session_id=session_id,
        latest_customer_message_override=latest_customer_message_override,
    )
    reply = build_reply_draft(prepared)
    can_fill_input = _can_fill_input(desktop_context)

    return {
        "ok": True,
        "prepared": prepared,
        "reply_draft": reply["reply_draft"],
        "reply_reasoning_summary": reply["reply_reasoning_summary"],
        "facts_used": reply["facts_used"],
        "ui_context_summary": _ui_context_summary(desktop_context),
        "safety": {
            "can_fill_input": can_fill_input,
            "auto_send_allowed": False,
        },
        "next_action": "fill_input" if can_fill_input else "manual_review",
    }
