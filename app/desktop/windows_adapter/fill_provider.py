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
    except Exception as exc:
        return build_fill_execution_result(
            executed=False,
            verified=False,
            target_name="",
            written_text="",
            verify_mode=verify_mode,
            reason=str(exc) or "fill_execution_failed",
        )

    written_text = str(result.get("written_text", ""))
    verification_method = str(result.get("verification_method", ""))
    diff_score = result.get("diff_score")
    diff_passed = result.get("diff_passed")
    diagnostics_path = str(result.get("diagnostics_path", ""))

    if verify_mode == "readback_required":
        verified = written_text == text
        reason = "" if verified else "readback_mismatch"
    elif verify_mode == "screenshot_diff_required":
        verified = bool(diff_passed)
        reason = "" if verified else str(result.get("reason", "")) or "screenshot_diff_failed"
    else:
        verified = False
        reason = "manual_review_required"

    return build_fill_execution_result(
        executed=True,
        verified=verified,
        target_name=str(result.get("target_name", "")),
        written_text=written_text,
        verify_mode=verify_mode,
        reason=reason,
        verification_method=verification_method,
        diff_score=diff_score if isinstance(diff_score, (int, float)) else None,
        diff_passed=bool(diff_passed) if diff_passed is not None else None,
        diagnostics_path=diagnostics_path,
    )
