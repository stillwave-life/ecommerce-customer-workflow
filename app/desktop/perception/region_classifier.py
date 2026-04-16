from __future__ import annotations

from typing import Any


REGION_MAP = {
    "conversation_list": "conversation_list_region",
    "chat": "chat_region",
    "product": "product_region",
    "user_order": "user_order_region",
    "input": "input_region",
    "send_button": "send_button_region",
}


def classify_regions(nodes: list[dict[str, Any]]) -> dict:
    regions = {value: [] for value in REGION_MAP.values()}
    for node in nodes:
        region_hint = str(node.get("region_hint", "")).strip()
        target = REGION_MAP.get(region_hint)
        if target:
            regions[target].append(node.copy())
    return {
        "ok": True,
        "regions": regions,
    }
