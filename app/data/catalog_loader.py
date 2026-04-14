from __future__ import annotations

import csv
import json
from pathlib import Path


def load_catalog_entries(config_path: str) -> list[dict]:
    config_file = Path(config_path)
    config = json.loads(config_file.read_text(encoding="utf-8"))
    catalog_rel_path = config.get("default_data_sources", {}).get("catalog")
    if not catalog_rel_path:
        return []

    catalog_path = (config_file.parent.parent / catalog_rel_path).resolve()
    if not catalog_path.is_file():
        return []

    with catalog_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return [dict(row) for row in reader]
