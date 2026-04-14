from __future__ import annotations

from pathlib import Path

from app.models import build_error_response, build_success_response


def _try_extract_text_candidates(_image_path: Path) -> list[dict]:
    return []


def parse_product_image(raw_path: str) -> dict:
    image_path = Path(raw_path).expanduser()
    if not image_path.is_file():
        return build_error_response("image path does not exist or is not a file")

    parsed_entities = _try_extract_text_candidates(image_path)
    page_context = {
        "image_path": str(image_path.resolve()),
        "file_name": image_path.name,
        "file_suffix": image_path.suffix.lower(),
        "ocr_status": "unavailable" if not parsed_entities else "parsed",
        "requires_manual_review": not bool(parsed_entities),
    }
    return build_success_response(
        page_context=page_context,
        parsed_entities=parsed_entities,
    )
