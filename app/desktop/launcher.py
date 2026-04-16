from __future__ import annotations

from typing import Any

from app.desktop.fill_action import build_fill_action
from app.desktop.reply_composer import compose_desktop_reply


def _is_jd_workspace(desktop_context: dict[str, Any]) -> bool:
    return desktop_context.get("platform") == "jd_customer_service" and float(desktop_context.get("confidence", 0.0)) >= 0.7


def launch_desktop_assistant(
    *,
    command: str,
    desktop_context: dict[str, Any],
    shop_id: str,
    session_id: str,
) -> dict[str, Any]:
    if command != "京东客服启动":
        return {"ok": False, "error": "unsupported desktop assistant command"}

    if not _is_jd_workspace(desktop_context):
        return {"ok": False, "error": "current screen is not recognized as jd customer service workspace"}

    reply = compose_desktop_reply(
        desktop_context,
        shop_id=shop_id,
        session_id=session_id,
    )
    fill_action = build_fill_action(reply.get("reply_draft", "")) if reply.get("next_action") == "fill_input" else None

    return {
        "ok": True,
        "command": command,
        "platform": desktop_context.get("platform"),
        "session_id": session_id,
        "reply": reply,
        "fill_action": fill_action,
        "ready_for_manual_send": bool(fill_action and fill_action.get("ready_for_manual_send")),
    }
