from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.desktop.launcher import launch_desktop_assistant
from scripts.jd_fill_with_ahk import fill_with_ahk


def configure_stdio() -> None:
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            reconfigure(encoding="utf-8")


def print_json(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False))


def minimal_desktop_context(latest_customer_message: str) -> dict[str, Any]:
    return {
        "platform": "jd_customer_service",
        "confidence": 0.9,
        "active_customer": {"id": "manual_user", "name": "manual_user"},
        "chat_context": {
            "latest_customer_message": latest_customer_message,
            "recent_messages": [],
            "contains_image": False,
        },
        "product_context": {"tab_active": False, "items": []},
        "user_order_context": {"user_labels": [], "orders": [], "service_forms": []},
        "input_context": {
            "editable": True,
            "has_smart_reply": False,
            "send_button_visible": True,
            "existing_text": "",
        },
    }


def extract_reply_draft(launch_result: dict[str, Any]) -> str:
    reply = launch_result.get("reply")
    if isinstance(reply, dict):
        for key in ("reply_draft", "text", "content"):
            value = reply.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    fill_action = launch_result.get("fill_action")
    if isinstance(fill_action, dict):
        for key in ("text", "value", "content"):
            value = fill_action.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    return ""


def main() -> None:
    if len(sys.argv) < 2:
        print_json({"ok": False, "reason": "missing_json_argument"})
        return

    raw_input = sys.argv[1]
    try:
        payload = json.loads(raw_input)
    except json.JSONDecodeError:
        latest_customer_message = raw_input.strip()
        payload = {
            "latest_customer_message": latest_customer_message,
            "desktop_context": minimal_desktop_context(latest_customer_message),
            "shop_id": "jd-default",
            "session_id": "desktop-session",
        }

    if not isinstance(payload, dict):
        print_json({"ok": False, "reason": "request_must_be_object"})
        return

    latest_customer_message = str(payload.get("latest_customer_message", "")).strip()
    desktop_context = payload.get("desktop_context")
    if not isinstance(desktop_context, dict):
        desktop_context = minimal_desktop_context(latest_customer_message)

    launch_result = launch_desktop_assistant(
        command="京东客服启动",
        desktop_context=desktop_context,
        shop_id=str(payload.get("shop_id", "jd-default")),
        session_id=str(payload.get("session_id", "desktop-session")),
        latest_customer_message=latest_customer_message or None,
    )
    if not launch_result.get("ok"):
        print_json(
            {
                "ok": False,
                "reason": "launch_failed",
                "launch_result": launch_result,
                "auto_send_allowed": False,
                "send_policy": "manual_only",
            }
        )
        return

    reply_draft = extract_reply_draft(launch_result)
    if not reply_draft:
        print_json(
            {
                "ok": False,
                "reason": "reply_draft_missing",
                "launch_result": launch_result,
                "auto_send_allowed": False,
                "send_policy": "manual_only",
            }
        )
        return

    ahk_path = payload.get("ahk_path")
    fill_result = fill_with_ahk(text=reply_draft, ahk_path=str(ahk_path) if ahk_path else None)
    print_json(
        {
            "ok": bool(fill_result.get("ok")),
            "reply_draft": reply_draft,
            "fill_result": fill_result,
            "diagnostics_path": fill_result.get("diagnostics_path"),
            "screenshots": fill_result.get("screenshots", {}),
            "requires_manual_confirmation": True,
            "fill_visually_confirmed": False,
            "auto_send_allowed": False,
            "send_policy": "manual_only",
        }
    )


if __name__ == "__main__":
    configure_stdio()
    main()
