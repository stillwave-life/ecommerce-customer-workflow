from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.models import build_error_response
from scripts.jd_customer_service_probe import build_probe_payload


def configure_stdio() -> None:
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            reconfigure(encoding="utf-8")


def print_json(payload: dict) -> None:
    print(json.dumps(payload, ensure_ascii=False))


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

    probe_payload = payload.get("probe_payload")
    if not isinstance(probe_payload, dict):
        print_json(build_error_response("probe_payload is required"))
        return

    probe_result = build_probe_payload(probe_payload)
    if not probe_result.get("ok"):
        print_json(probe_result)
        return

    export_payload = {
        "ok": True,
        "export": {
            "probe_result": probe_result.get("probe_result"),
            "diagnostics_report": probe_result.get("diagnostics_report"),
            "desktop_context": probe_result.get("desktop_context"),
            "focus_result": probe_result.get("focus_result"),
        },
    }
    print_json(export_payload)


if __name__ == "__main__":
    configure_stdio()
    main()
