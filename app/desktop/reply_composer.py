from __future__ import annotations

from typing import Any

from app.desktop.prepare_mapper import build_prepared_from_desktop_context
from app.reply.reply_builder import build_reply_draft


def _can_fill_input(desktop_context: dict[str, Any]) -> bool:
    input_context = desktop_context.get("input_context") or {}
    return bool(input_context.get("editable")) and bool(input_context.get("send_button_visible"))


def compose_desktop_reply(
    desktop_context: dict[str, Any],
    *,
    shop_id: str,
    session_id: str,
) -> dict[str, Any]:
    prepared = build_prepared_from_desktop_context(
        desktop_context,
        shop_id=shop_id,
        session_id=session_id,
    )
    reply = build_reply_draft(prepared)
    can_fill_input = _can_fill_input(desktop_context)

    return {
        "ok": True,
        "prepared": prepared,
        "reply_draft": reply["reply_draft"],
        "reply_reasoning_summary": reply["reply_reasoning_summary"],
        "facts_used": reply["facts_used"],
        "safety": {
            "can_fill_input": can_fill_input,
            "auto_send_allowed": False,
        },
        "next_action": "fill_input" if can_fill_input else "manual_review",
    }
