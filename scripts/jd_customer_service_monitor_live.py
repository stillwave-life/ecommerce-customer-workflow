from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.desktop.monitor_once import build_monitor_once_result
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
    print_json(
        build_monitor_once_result(
            probe_result,
            previous_message=str(payload.get("previous_message", "")),
            shop_id=str(payload.get("shop_id", "jd-default")),
            session_id=str(payload.get("session_id", "desktop-session")),
        )
    )


if __name__ == "__main__":
    configure_stdio()
    main()
