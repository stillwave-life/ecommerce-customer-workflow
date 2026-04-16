from __future__ import annotations


def build_probe_diagnostics(
    *,
    window: dict,
    node_count: int,
    editable_node_count: int,
    clickable_node_count: int,
    visible_node_count: int,
) -> dict:
    return {
        "ok": True,
        "window": window.copy(),
        "node_stats": {
            "node_count": node_count,
            "editable_node_count": editable_node_count,
            "clickable_node_count": clickable_node_count,
            "visible_node_count": visible_node_count,
        },
    }
