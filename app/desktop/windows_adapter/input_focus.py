from __future__ import annotations


def build_focus_result(
    *,
    focused: bool,
    target_role: str,
    target_name: str,
    reason: str,
) -> dict:
    return {
        "ok": focused,
        "focused": focused,
        "target_role": target_role,
        "target_name": target_name,
        "reason": reason,
    }
