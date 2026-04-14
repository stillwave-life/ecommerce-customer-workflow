import json
import sys

REQUIRED_FIELDS = ["shop_id", "session_id", "product_ref", "user_message"]
REQUIRED_PRODUCT_REF_FIELDS = ["type", "value"]


def configure_stdio():
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        if stream is None:
            continue
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            reconfigure(encoding="utf-8")


def error(message):
    print(json.dumps({"ok": False, "error": message}, ensure_ascii=False))
    sys.exit(0)


def normalize_string(value):
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized or None


def main():
    if len(sys.argv) < 2:
        error("missing JSON argument")

    raw = sys.argv[1]

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        error(f"invalid JSON: {exc.msg}")

    if not isinstance(payload, dict):
        error("request must be a JSON object")

    missing = [field for field in REQUIRED_FIELDS if field not in payload]
    if missing:
        error("missing required fields: " + ", ".join(missing))

    shop_id = normalize_string(payload.get("shop_id"))
    session_id = normalize_string(payload.get("session_id"))
    user_message = normalize_string(payload.get("user_message"))
    product_ref = payload.get("product_ref")

    invalid = []
    if not shop_id:
        invalid.append("shop_id")
    if not session_id:
        invalid.append("session_id")
    if not user_message:
        invalid.append("user_message")
    if not isinstance(product_ref, dict):
        error("product_ref must be an object")

    missing_product_ref = [field for field in REQUIRED_PRODUCT_REF_FIELDS if field not in product_ref]
    if missing_product_ref:
        error("missing product_ref fields: " + ", ".join(missing_product_ref))

    product_type = normalize_string(product_ref.get("type"))
    product_value = normalize_string(product_ref.get("value"))

    if not product_type:
        invalid.append("product_ref.type")
    if not product_value:
        invalid.append("product_ref.value")

    if invalid:
        error("invalid required fields: " + ", ".join(invalid))

    normalized = {
        "shop_id": shop_id,
        "session_id": session_id,
        "product_ref": {
            "type": product_type.lower(),
            "value": product_value,
        },
        "user_message": user_message,
    }

    print(json.dumps({"ok": True, "normalized": normalized}, ensure_ascii=False))


if __name__ == "__main__":
    configure_stdio()
    main()
