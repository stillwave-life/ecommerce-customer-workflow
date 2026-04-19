import json
import os
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
SCRIPT = ROOT_DIR / "scripts" / "jd_customer_service_start.py"
PROBE_SCRIPT = ROOT_DIR / "scripts" / "jd_customer_service_probe.py"


def test_jd_customer_service_start_accepts_desktop_context_payload():
    payload = {
        "command": "京东客服启动",
        "shop_id": "shop_001",
        "session_id": "desktop-session-1",
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
    assert response["fill_action"]["send_policy"] == "manual_only"
    assert response["fill_action"]["auto_send_allowed"] is False


def test_jd_customer_service_start_rejects_missing_context():
    payload = {"command": "京东客服启动", "shop_id": "shop_001", "session_id": "desktop-session-1"}

    result = subprocess.run(
        [sys.executable, str(SCRIPT), json.dumps(payload, ensure_ascii=False)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="strict",
        check=False,
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    )

    response = json.loads(result.stdout)
    assert response["ok"] is False
    assert response["error"] == "desktop_context is required"


def test_jd_customer_service_probe_outputs_diagnostics_and_context():
    payload = {
        "window": {
            "handle": 1001,
            "title": "evw10158991",
            "process_name": "jd-workbench.exe",
            "bounds": [0, 0, 1680, 1048],
            "is_foreground": True,
        },
        "active_customer": {"id": "jd_4a3d4c80e30ef", "name": "jd_4a3d4c80e30ef"},
        "nodes": [
            {
                "role": "edit",
                "name": "输入框",
                "text": "",
                "bounds": [360, 690, 970, 1010],
                "editable": True,
                "clickable": True,
                "visible": True,
                "automation_id": "reply-editor",
                "control_type": "Edit",
                "class_name": "RichEdit",
                "enabled": True,
                "path": ["window", "footer", "reply_editor"],
            },
            {
                "role": "text",
                "name": "客户消息",
                "text": "这款还有吗？",
                "bounds": [380, 320, 900, 420],
                "editable": False,
                "clickable": False,
                "visible": True,
                "control_type": "Text",
                "path": ["window", "chat_panel", "message_list"],
            },
            {
                "role": "button",
                "name": "发送(F1)",
                "text": "发送(F1)",
                "bounds": [1200, 920, 1320, 980],
                "editable": False,
                "clickable": True,
                "visible": True,
                "automation_id": "send-btn",
                "control_type": "Button",
                "enabled": True,
                "path": ["window", "footer", "send_button"],
            },
        ],
    }

    result = subprocess.run(
        [sys.executable, str(PROBE_SCRIPT), json.dumps(payload, ensure_ascii=False)],
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
    assert response["probe_result"]["process_name"] == "jd-workbench.exe"
    assert response["diagnostics_report"]["backend"]["type"] == "windows_uia"
    assert response["desktop_context"]["platform"] == "jd_customer_service"
    assert response["focus_result"]["focused"] is True


def test_jd_customer_service_probe_accepts_live_backend_flag():
    payload = {"backend": {"type": "windows_uia", "live": True}}

    result = subprocess.run(
        [sys.executable, str(PROBE_SCRIPT), json.dumps(payload, ensure_ascii=False)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="strict",
        check=False,
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    )

    assert result.returncode == 0
    response = json.loads(result.stdout)
    assert response["backend"]["live"] is True


def test_jd_customer_service_probe_returns_unavailable_when_live_backend_missing():
    payload = {"backend": {"type": "windows_uia", "live": True}}

    result = subprocess.run(
        [sys.executable, str(PROBE_SCRIPT), json.dumps(payload, ensure_ascii=False)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="strict",
        check=False,
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    )

    assert result.returncode == 0
    response = json.loads(result.stdout)
    assert response["ok"] is False
    assert response["error"] == "windows_uia_import_failed"
    assert response["backend"]["live"] is True
