import json
import os
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
SCRIPT = ROOT_DIR / "scripts" / "jd_customer_service_monitor_live.py"


def test_jd_customer_service_monitor_live_returns_idle_for_same_message():
    payload = {
        "probe_payload": {
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
            ],
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


def test_jd_customer_service_monitor_live_returns_new_message_reply():
    payload = {
        "probe_payload": {
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
