from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.desktop.launcher import launch_desktop_assistant
from app.desktop.windows_adapter.fill_provider import execute_fill_with_provider
from app.desktop.windows_adapter.pywinauto_fill_backend import build_fill_provider
from app.models import build_error_response


def configure_stdio() -> None:
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            reconfigure(encoding="utf-8")


def print_json(payload: dict) -> None:
    print(json.dumps(payload, ensure_ascii=False))


def _minimal_desktop_context(latest_customer_message: str) -> dict:
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


def _structured_failure(*, reply: dict | None = None, fill_action: dict | None = None, right_panel_actions: list | None = None, reason: str, fill_result: dict | None = None) -> dict:
    return {
        "ok": False,
        "reason": reason,
        "reply": reply or {},
        "fill_action": fill_action or {},
        "fill_result": fill_result or {"ok": False, "reason": reason},
        "right_panel_actions": right_panel_actions or [],
    }


def main() -> None:
    if len(sys.argv) < 2:
        print_json(build_error_response("missing JSON argument"))
        return

    try:
        payload = json.loads(sys.argv[1])
    except json.JSONDecodeError as exc:
        print_json(build_error_response(f"invalid JSON: {exc.msg}"))
        return

    if not isinstance(payload, dict):
        print_json(build_error_response("request must be a JSON object"))
        return

    latest_customer_message = str(payload.get("latest_customer_message", "")).strip()
    desktop_context = payload.get("desktop_context")
    if not isinstance(desktop_context, dict):
        desktop_context = _minimal_desktop_context(latest_customer_message)

    launch_result = launch_desktop_assistant(
        command="京东客服启动",
        desktop_context=desktop_context,
        shop_id=str(payload.get("shop_id", "jd-default")),
        session_id=str(payload.get("session_id", "desktop-session")),
        latest_customer_message=latest_customer_message or None,
    )

    reply = launch_result.get("reply") if isinstance(launch_result.get("reply"), dict) else {}
    fill_action = launch_result.get("fill_action") if isinstance(launch_result.get("fill_action"), dict) else {}
    right_panel_actions = launch_result.get("right_panel_actions") if isinstance(launch_result.get("right_panel_actions"), list) else []

    if not launch_result.get("ok"):
        print_json(
            _structured_failure(
                reply=reply,
                fill_action=fill_action,
                right_panel_actions=right_panel_actions,
                reason=str(launch_result.get("error", "launch_failed")),
            )
        )
        return

    if not fill_action:
        print_json(
            _structured_failure(
                reply=reply,
                fill_action=fill_action,
                right_panel_actions=right_panel_actions,
                reason="fill_action_missing",
            )
        )
        return

    fill_action["auto_send_allowed"] = False
    fill_action["send_policy"] = "manual_only"

    try:
        provider = build_fill_provider()
    except Exception:
        print_json(
            _structured_failure(
                reply=reply,
                fill_action=fill_action,
                right_panel_actions=right_panel_actions,
                reason="fill_provider_unavailable",
                fill_result={"ok": False, "executed": False, "verified": False, "reason": "fill_provider_unavailable"},
            )
        )
        return

    fill_result = execute_fill_with_provider(fill_action, provider=provider)
    print_json(
        {
            "ok": bool(fill_result.get("ok")),
            "reply": reply,
            "fill_action": fill_action,
            "fill_result": fill_result,
            "right_panel_actions": right_panel_actions,
        }
    )


if __name__ == "__main__":
    configure_stdio()
    main()
