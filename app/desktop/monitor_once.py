from __future__ import annotations

from typing import Any

from app.desktop.fill_action import build_fill_action
from app.desktop.reply_composer import compose_desktop_reply
from app.models import build_error_response


def _latest_message(desktop_context: dict[str, Any]) -> str:
    chat_context = desktop_context.get("chat_context") or {}
    return str(chat_context.get("latest_customer_message", "")).strip()


def build_monitor_once_result(
    probe_result: dict[str, Any],
    *,
    previous_message: str,
    shop_id: str,
    session_id: str,
) -> dict[str, Any]:
    if not probe_result.get("ok"):
        return build_error_response(str(probe_result.get("error", "probe failed")), status="error")

    desktop_context = probe_result.get("desktop_context")
    if not isinstance(desktop_context, dict):
        return build_error_response("desktop_context is required", status="error")

    latest_message = _latest_message(desktop_context)
    if not latest_message or latest_message == previous_message:
        return {
            "ok": True,
            "status": "idle",
            "desktop_context": desktop_context,
            "latest_message": latest_message,
            "reply": None,
            "fill_action": None,
        }

    reply = compose_desktop_reply(desktop_context, shop_id=shop_id, session_id=session_id)
    focus_result = probe_result.get("focus_result") or {}
    fill_action = None
    if reply.get("next_action") == "fill_input":
        fill_action = build_fill_action(
            reply.get("reply_draft", ""),
            target="reply_box",
            target_bounds=focus_result.get("target_bounds") or [],
            target_automation_id=str(focus_result.get("target_automation_id", "")),
            verify_mode="readback_required",
        )

    return {
        "ok": True,
        "status": "new_message",
        "desktop_context": desktop_context,
        "latest_message": latest_message,
        "reply": reply,
        "fill_action": fill_action,
    }
