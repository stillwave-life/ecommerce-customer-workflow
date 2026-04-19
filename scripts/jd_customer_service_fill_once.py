from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.desktop.windows_adapter.fill_executor import build_fill_execution_result
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


def _unavailable_result(fill_action: dict) -> dict:
    return build_fill_execution_result(
        executed=False,
        verified=False,
        target_name="",
        written_text="",
        verify_mode=str(fill_action.get("verify_mode", "manual_review")),
        reason="fill_provider_unavailable",
    )


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

    fill_action = payload.get("fill_action")
    if not isinstance(fill_action, dict):
        print_json(build_error_response("fill_action is required"))
        return

    try:
        provider = build_fill_provider()
    except Exception:
        print_json(_unavailable_result(fill_action))
        return

    print_json(execute_fill_with_provider(fill_action, provider=provider))


if __name__ == "__main__":
    configure_stdio()
    main()
