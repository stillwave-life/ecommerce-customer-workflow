from __future__ import annotations

from collections.abc import Callable
from typing import Any


def _backend_metadata() -> dict[str, Any]:
    return {"type": "windows_uia", "live": True}


def _valid_snapshot(snapshot: Any) -> bool:
    return (
        isinstance(snapshot, dict)
        and isinstance(snapshot.get("window"), dict)
        and isinstance(snapshot.get("nodes"), list)
        and all(isinstance(node, dict) for node in snapshot.get("nodes", []))
    )


def _should_keep_node(node: dict[str, Any]) -> bool:
    if node.get("children"):
        return True
    if node.get("visible") and (node.get("editable") or node.get("clickable")):
        return True
    if str(node.get("text", "")).strip():
        return True
    if str(node.get("value", "")).strip():
        return True
    if str(node.get("name", "")).strip() and node.get("visible", True):
        return True
    return False


def _filter_nodes(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    filtered = []
    for node in nodes:
        item = node.copy()
        children = item.get("children") or []
        item["children"] = _filter_nodes([child for child in children if isinstance(child, dict)])
        if _should_keep_node(item):
            filtered.append(item)
    return filtered


def collect_live_uia_snapshot(provider: Callable[[], dict[str, Any]] | None = None) -> dict[str, Any]:
    backend = _backend_metadata()
    if provider is None:
        from app.desktop.windows_adapter.windows_uia_provider import collect_windows_uia_snapshot

        return collect_windows_uia_snapshot()

    snapshot = provider()
    if not _valid_snapshot(snapshot):
        return {
            "ok": False,
            "error": "invalid_windows_uia_snapshot",
            "backend": backend,
        }

    return {
        "ok": True,
        "backend": backend,
        "window": snapshot["window"].copy(),
        "nodes": _filter_nodes(snapshot["nodes"]),
    }
