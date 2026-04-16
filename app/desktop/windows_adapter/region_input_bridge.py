from __future__ import annotations

from typing import Any


def build_region_input_nodes(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [node.copy() for node in nodes]
