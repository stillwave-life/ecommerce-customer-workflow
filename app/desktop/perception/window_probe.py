from __future__ import annotations


def build_window_probe_result(
    *,
    window_title: str,
    process_name: str,
    window_bounds: list[int],
    is_foreground: bool,
    platform_hint: str,
    confidence: float,
) -> dict:
    return {
        "ok": True,
        "window_title": window_title,
        "process_name": process_name,
        "window_bounds": list(window_bounds),
        "is_foreground": is_foreground,
        "platform_hint": platform_hint,
        "confidence": confidence,
    }
