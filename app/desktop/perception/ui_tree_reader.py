from __future__ import annotations

from typing import Any


def _copy_nodes(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [node.copy() for node in nodes]


def build_ui_tree_result(*, nodes: list[dict[str, Any]]) -> dict:
    return {
        "ok": True,
        "nodes": _copy_nodes(nodes),
    }
