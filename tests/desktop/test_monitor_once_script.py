import json
import os
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
SCRIPT = ROOT_DIR / "scripts" / "jd_customer_service_monitor_once.py"


def test_jd_customer_service_monitor_once_returns_idle_for_same_message():
    payload = {
        "probe_result": {
            "ok": True,
            "desktop_context": {
                "chat_context": {"latest_customer_message": "这款还有吗？"},
                "input_context": {"editable": True, "send_button_visible": True},
            },
            "focus_result": {"focused": True},
        },
        "previous_message": "这款还有吗？",
        "shop_id": "shop_001",
        "session_id": "desktop-session-1",
    }

    result = subprocess.run(
        [sys.executable, str(SCRIPT), json.dumps(payload, ensure_ascii=False)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="strict",
        check=False,
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    )

    assert result.returncode == 0
    response = json.loads(result.stdout)
    assert response["ok"] is True
    assert response["status"] == "idle"


def test_jd_customer_service_monitor_once_returns_new_message_reply():
    payload = {
        "probe_result": {
            "ok": True,
            "desktop_context": {
                "platform": "jd_customer_service",
                "confidence": 0.9,
                "active_customer": {"id": "jd_4a3d4c80e30ef", "name": "jd_4a3d4c80e30ef"},
                "chat_context": {
                    "latest_customer_message": "这款还有吗？",
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
            },
            "focus_result": {
                "focused": True,
                "target_bounds": [360, 690, 970, 1010],
                "target_automation_id": "reply-editor",
            },
        },
        "previous_message": "",
        "shop_id": "shop_001",
        "session_id": "desktop-session-1",
    }

    result = subprocess.run(
        [sys.executable, str(SCRIPT), json.dumps(payload, ensure_ascii=False)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="strict",
        check=False,
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    )

    assert result.returncode == 0
    response = json.loads(result.stdout)
    assert response["ok"] is True
    assert response["status"] == "new_message"
    assert response["reply"]["reply_draft"]
    assert response["fill_action"]["target_automation_id"] == "reply-editor"
