from __future__ import annotations


def build_fill_action(reply_text: str, *, target: str = "reply_box") -> dict:
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
        "text": text,
        "send_policy": "manual_only",
        "ready_for_manual_send": True,
        "auto_send_allowed": False,
    }
