from __future__ import annotations


def build_fill_execution_result(
    *,
    executed: bool,
    verified: bool,
    target_name: str,
    written_text: str,
    verify_mode: str,
    reason: str,
    verification_method: str = "",
    diff_score: float | None = None,
    diff_passed: bool | None = None,
    diagnostics_path: str = "",
) -> dict:
    return {
        "ok": executed and verified,
        "executed": executed,
        "verified": verified,
        "target_name": target_name,
        "written_text": written_text,
        "verify_mode": verify_mode,
        "reason": reason,
        "verification_method": verification_method,
        "diff_score": diff_score,
        "diff_passed": diff_passed,
        "diagnostics_path": diagnostics_path,
    }
