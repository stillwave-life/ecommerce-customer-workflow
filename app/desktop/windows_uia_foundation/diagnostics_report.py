from __future__ import annotations


def build_diagnostics_report(
    *,
    window: dict,
    node_stats: dict,
    input_candidates: list[dict],
    gate_result: dict,
    focus_result: dict,
    desktop_context: dict,
) -> dict:
    return {
        "window": window.copy(),
        "node_stats": node_stats.copy(),
        "input_candidates": [item.copy() for item in input_candidates],
        "gate_result": gate_result.copy(),
        "focus_result": focus_result.copy(),
        "desktop_context": desktop_context.copy(),
    }
