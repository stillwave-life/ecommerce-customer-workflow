from __future__ import annotations

import re
from urllib.parse import urlparse

from app.models import build_error_response, build_product_ref, build_success_response

JD_HOST_SUFFIXES = ("jd.com", "3.cn")
PRODUCT_ID_PATTERN = re.compile(r"/(\d+)\.html(?:$|[?#])")


def parse_product_url(raw_url: str) -> dict:
    parsed = urlparse(raw_url)
    hostname = (parsed.hostname or "").lower()
    if not hostname or not any(hostname == suffix or hostname.endswith(f'.{suffix}') for suffix in JD_HOST_SUFFIXES):
        return build_error_response("only jd product urls are supported in this mvp")

    match = PRODUCT_ID_PATTERN.search(parsed.path)
    if not match:
        return build_error_response("unable to extract jd product id from url")

    product_id = match.group(1)
    product_ref = build_product_ref("product_id", product_id)
    page_context = {
        "url": raw_url,
        "hostname": hostname,
        "path": parsed.path,
    }
    parsed_entities = [
        {"type": "product_id", "value": product_id, "source": "url"},
    ]
    return build_success_response(
        product_ref=product_ref,
        page_context=page_context,
        parsed_entities=parsed_entities,
    )
