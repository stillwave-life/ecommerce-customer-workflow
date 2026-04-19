from __future__ import annotations


def build_fill_action(
    reply_text: str,
    *,
    target: str = "reply_box",
    target_bounds: list[int] | None = None,
    target_automation_id: str = "",
    verify_mode: str = "manual_review",
) -> dict:
    text = reply_text.strip()
    if not text:
        return {
            "ok": False,
            "error": "reply text is required",
            "auto_send_allowed": False,
        }

    return {
        "ok": True,
        "action": "fill_input",
        "target": target,
        "target_bounds": list(target_bounds or []),
        "target_automation_id": target_automation_id,
        "text": text,
        "send_policy": "manual_only",
        "verify_mode": verify_mode,
        "ready_for_manual_send": True,
        "auto_send_allowed": False,
    }
