from __future__ import annotations


def build_focus_result(
    *,
    focused: bool,
    target_role: str,
    target_name: str,
    reason: str,
    target_bounds: list[int] | None = None,
    target_automation_id: str = "",
) -> dict:
    return {
        "ok": focused,
        "focused": focused,
        "target_role": target_role,
        "target_name": target_name,
        "reason": reason,
        "target_bounds": list(target_bounds or []),
        "target_automation_id": target_automation_id,
    }
