import json
import os
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
SCRIPT = ROOT_DIR / "scripts" / "jd_customer_service_generate_and_fill.py"


def test_generate_and_fill_builds_minimal_context_when_missing():
    payload = {
        "shop_id": "shop_001",
        "session_id": "desktop-session-1",
        "latest_customer_message": "这款还有吗？",
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
    assert response["ok"] is False
    assert response["reply"]["prepared"]["user_message"] == "这款还有吗？"
    assert response["fill_action"]["send_policy"] == "manual_only"
    assert response["fill_action"]["auto_send_allowed"] is False
    assert response["reason"] == "fill_provider_unavailable"
