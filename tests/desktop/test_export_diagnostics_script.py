import json
import os
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
SCRIPT = ROOT_DIR / "scripts" / "jd_customer_service_export_diagnostics.py"


def test_jd_customer_service_export_diagnostics_returns_export_payload():
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
        }
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
    assert response["export"]["diagnostics_report"]["backend"]["type"] == "windows_uia"
    assert response["export"]["desktop_context"]["platform"] == "jd_customer_service"
