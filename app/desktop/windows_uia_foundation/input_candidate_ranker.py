from __future__ import annotations

from typing import Any


def _score_node(node: dict[str, Any]) -> tuple[float, list[str]]:
    score = 0.0
    reasons: list[str] = []

    if node.get("editable"):
        score += 0.4
        reasons.append("editable")

    bounds = node.get("bounds") or [0, 0, 0, 0]
    top = bounds[1] if len(bounds) >= 2 else 0
    bottom = bounds[3] if len(bounds) >= 4 else 0
    height = max(0, bottom - top)

    if top >= 600:
        score += 0.3
        reasons.append("bottom_region")

    if height >= 200:
        score += 0.2
        reasons.append("large_text_area")

    name = str(node.get("name", "")).strip()
    if "搜索" in name:
        score -= 0.2
        reasons.append("search_penalty")

    return score, reasons


def rank_input_candidates(nodes: list[dict[str, Any]]) -> dict:
    candidates = []
    for node in nodes:
        score, reasons = _score_node(node)
        candidates.append({"node": node.copy(), "score": score, "reasons": reasons})
    candidates.sort(key=lambda item: item["score"], reverse=True)
    return {"ok": True, "candidates": candidates}
