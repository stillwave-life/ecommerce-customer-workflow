from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.data.knowledge_loader import load_knowledge_hits
from app.models import build_error_response, build_prepared_result, build_success_response, normalize_string
from app.parsers.image_parser import parse_product_image
from app.parsers.url_parser import parse_product_url

CONFIG_PATH = ROOT_DIR / "config" / "default.json"
SUPPORTED_SOURCE_TYPES = {"text", "url", "image"}


def configure_stdio() -> None:
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            reconfigure(encoding="utf-8")


def print_json(payload: dict) -> None:
    print(json.dumps(payload, ensure_ascii=False))


def parse_input_argument(raw: str) -> dict:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        return build_error_response(f"invalid JSON: {exc.msg}")
    if not isinstance(payload, dict):
        return build_error_response("request must be a JSON object")
    return build_success_response(payload=payload)


def normalize_base_fields(payload: dict) -> tuple[str | None, str | None, str | None, str | None]:
    shop_id = normalize_string(payload.get("shop_id"))
    session_id = normalize_string(payload.get("session_id"))
    source_type = normalize_string(payload.get("source_type"))
    source_value = normalize_string(payload.get("source_value"))
    return shop_id, session_id, source_type, source_value


def derive_text_source_value(payload: dict) -> str | None:
    source_value = normalize_string(payload.get("source_value"))
    if source_value:
        return source_value
    product_ref = payload.get("product_ref")
    if isinstance(product_ref, dict):
        return normalize_string(product_ref.get("value"))
    return None


def main() -> None:
    if len(sys.argv) < 2:
        print_json(build_error_response("missing JSON argument"))
        return

    parsed = parse_input_argument(sys.argv[1])
    if not parsed.get("ok"):
        print_json(parsed)
        return

    payload = parsed["payload"]
    shop_id, session_id, source_type, source_value = normalize_base_fields(payload)
    user_message = normalize_string(payload.get("user_message"))

    missing = []
    if not shop_id:
        missing.append("shop_id")
    if not session_id:
        missing.append("session_id")
    if not user_message:
        missing.append("user_message")
    if missing:
        print_json(build_error_response("invalid required fields: " + ", ".join(missing)))
        return

    if not source_type:
        source_type = "text" if payload.get("source_value") or payload.get("product_ref") else None
    if not source_type or source_type not in SUPPORTED_SOURCE_TYPES:
        print_json(build_error_response("source_type must be one of: text, url, image"))
        return

    if source_type == "text":
        source_value = derive_text_source_value(payload)
    if not source_value:
        print_json(build_error_response("source_value is required for the selected source_type"))
        return

    product_ref = payload.get("product_ref") if isinstance(payload.get("product_ref"), dict) else None
    page_context = {}
    parsed_entities = []

    if source_type == "url":
        result = parse_product_url(source_value)
        if not result.get("ok"):
            print_json(result)
            return
        product_ref = result.get("product_ref")
        page_context = result.get("page_context") or {}
        parsed_entities = result.get("parsed_entities") or []
    elif source_type == "image":
        result = parse_product_image(source_value)
        if not result.get("ok"):
            print_json(result)
            return
        page_context = result.get("page_context") or {}
        parsed_entities = result.get("parsed_entities") or []
    else:
        page_context = {"input_mode": "text"}

    knowledge_hits = load_knowledge_hits(
        config_path=str(CONFIG_PATH),
        product_ref=product_ref,
        parsed_entities=parsed_entities,
    )

    prepared = build_prepared_result(
        shop_id=shop_id,
        session_id=session_id,
        source_type=source_type,
        source_value=source_value,
        user_message=user_message,
        product_ref=product_ref,
        page_context=page_context,
        parsed_entities=parsed_entities,
        knowledge_hits=knowledge_hits,
    )
    response = build_success_response(
        prepared=prepared,
        action_plan=["review_prepared_request", "generate_reply"],
    )
    print_json(response)


if __name__ == "__main__":
    configure_stdio()
    main()
