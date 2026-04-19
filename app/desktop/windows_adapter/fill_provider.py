from __future__ import annotations

from collections.abc import Callable
from typing import Any

from app.desktop.windows_adapter.fill_executor import build_fill_execution_result


FillProvider = Callable[[dict[str, Any]], dict[str, Any]]


def execute_fill_with_provider(action: dict[str, Any], *, provider: FillProvider) -> dict[str, Any]:
    text = str(action.get("text", "")).strip()
    verify_mode = str(action.get("verify_mode", "manual_review"))
    if not text:
        return build_fill_execution_result(
            executed=False,
            verified=False,
            target_name="",
            written_text="",
            verify_mode=verify_mode,
            reason="reply text is required",
        )

    try:
        result = provider(action)
    except Exception:
        return build_fill_execution_result(
            executed=False,
            verified=False,
            target_name="",
            written_text="",
            verify_mode=verify_mode,
            reason="fill_execution_failed",
        )

    written_text = str(result.get("written_text", ""))
    verified = verify_mode != "readback_required" or written_text == text
    return build_fill_execution_result(
        executed=True,
        verified=verified,
        target_name=str(result.get("target_name", "")),
        written_text=written_text,
        verify_mode=verify_mode,
        reason="" if verified else "readback_mismatch",
    )
