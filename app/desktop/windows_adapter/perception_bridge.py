from __future__ import annotations


def build_windows_perception_result(
    *,
    probe_result: dict,
    desktop_context: dict,
    focus_result: dict,
) -> dict:
    return {
        "ok": True,
        "probe_result": probe_result,
        "desktop_context": desktop_context,
        "focus_result": focus_result,
    }
