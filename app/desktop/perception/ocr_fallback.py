from __future__ import annotations


def build_ocr_fallback_request(
    *,
    missing_fields: list[str],
    screenshot_path: str,
    region_names: list[str],
) -> dict:
    return {
        "ok": True,
        "missing_fields": list(missing_fields),
        "screenshot_path": screenshot_path,
        "region_names": list(region_names),
    }
