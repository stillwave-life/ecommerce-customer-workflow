from __future__ import annotations


def build_windows_perception_result(
    *,
    probe_result: dict,
    desktop_context: dict,
    focus_result: dict,
    diagnostics_report: dict | None = None,
) -> dict:
    result = {
        "ok": True,
        "probe_result": probe_result,
        "desktop_context": desktop_context,
        "focus_result": focus_result,
    }
    if diagnostics_report is not None:
        result["diagnostics_report"] = diagnostics_report
    return result
