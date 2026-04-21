from __future__ import annotations

DEFAULT_INPUT_BOUNDS = [0.18, 0.82, 0.80, 0.96]


def build_fill_action(
    reply_text: str,
    *,
    target: str = "reply_box",
    target_bounds: list[int] | list[float] | None = None,
    target_automation_id: str = "",
    verify_mode: str = "screenshot_diff_required",
    targeting_strategy: str = "coordinates",
    clear_before_fill: bool = True,
    paste_via_clipboard: bool = True,
    window_title_hint: str = "咚咚融合工作台",
    ui_profile: str = "jd_maximized_default",
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
        "target_bounds": list(target_bounds or DEFAULT_INPUT_BOUNDS),
        "target_automation_id": target_automation_id,
        "text": text,
        "targeting_strategy": targeting_strategy,
        "clear_before_fill": clear_before_fill,
        "paste_via_clipboard": paste_via_clipboard,
        "window_title_hint": window_title_hint,
        "ui_profile": ui_profile,
        "send_policy": "manual_only",
        "verify_mode": verify_mode,
        "ready_for_manual_send": True,
        "auto_send_allowed": False,
    }
