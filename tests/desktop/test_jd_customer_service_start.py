import json
import os
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
SCRIPT = ROOT_DIR / "scripts" / "jd_customer_service_start.py"


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
