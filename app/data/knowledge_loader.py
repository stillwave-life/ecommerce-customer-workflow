from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.data.catalog_loader import load_catalog_entries


def _load_text_file(path: Path) -> str:
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")


def _collect_candidate_values(product_ref: dict[str, str] | None, parsed_entities: list[dict[str, Any]]) -> list[str]:
    candidates: list[str] = []
    if product_ref and product_ref.get("value"):
        candidates.append(str(product_ref["value"]))
    for entity in parsed_entities:
        value = entity.get("value")
        if value:
            candidates.append(str(value))
    return [candidate for candidate in dict.fromkeys(candidates) if candidate]


def _match_catalog_entries(entries: list[dict[str, Any]], candidates: list[str]) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for entry in entries:
        haystack = " ".join(str(value) for value in entry.values() if value is not None)
        for candidate in candidates:
            if candidate and candidate in haystack:
                for field, value in entry.items():
                    if value:
                        hits.append({"source": "catalog", "field": field, "value": str(value)})
                break
    return hits


def _match_text_block(block_name: str, content: str, candidates: list[str]) -> list[dict[str, Any]]:
    if not content.strip():
        return []
    lines = [line.strip() for line in content.splitlines() if line.strip()]
    hits: list[dict[str, Any]] = []
    for line in lines:
        for candidate in candidates:
            if candidate and candidate in line:
                hits.append({"source": block_name, "field": "matched_line", "value": line})
                break
    return hits


def load_knowledge_hits(
    *,
    config_path: str,
    product_ref: dict[str, str] | None,
    parsed_entities: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    config_file = Path(config_path)
    config = json.loads(config_file.read_text(encoding="utf-8"))
    data_sources = config.get("default_data_sources", {})
    base_dir = config_file.parent.parent

    candidates = _collect_candidate_values(product_ref, parsed_entities)
    catalog_entries = load_catalog_entries(str(config_file))
    faq_text = _load_text_file((base_dir / data_sources.get("faq", "")).resolve()) if data_sources.get("faq") else ""
    rules_text = _load_text_file((base_dir / data_sources.get("rules", "")).resolve()) if data_sources.get("rules") else ""

    return {
        "catalog": _match_catalog_entries(catalog_entries, candidates),
        "faq": _match_text_block("faq", faq_text, candidates),
        "rules": _match_text_block("rules", rules_text, candidates),
    }
