import json
import os
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
SCRIPT = ROOT_DIR / "scripts" / "jd_customer_service_fill_once.py"


def test_jd_customer_service_fill_once_reports_unavailable_without_provider():
    payload = {
        "fill_action": {
            "text": "你好",
            "verify_mode": "readback_required",
            "target_automation_id": "reply-editor",
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
    assert response["ok"] is False
    assert response["reason"] in {"fill_provider_unavailable", "fill_execution_failed"}
