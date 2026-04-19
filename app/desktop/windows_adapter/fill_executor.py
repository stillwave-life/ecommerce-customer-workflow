from __future__ import annotations


def build_fill_execution_result(
    *,
    executed: bool,
    verified: bool,
    target_name: str,
    written_text: str,
    verify_mode: str,
    reason: str,
) -> dict:
    return {
        "ok": executed and verified,
        "executed": executed,
        "verified": verified,
        "target_name": target_name,
        "written_text": written_text,
        "verify_mode": verify_mode,
        "reason": reason,
    }
