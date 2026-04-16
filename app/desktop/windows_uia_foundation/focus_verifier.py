from __future__ import annotations


def build_focus_verification(*, focused: bool, target_name: str, reason: str = "") -> dict:
    return {
        "ok": focused,
        "focused": focused,
        "target_name": target_name,
        "reason": reason,
    }
