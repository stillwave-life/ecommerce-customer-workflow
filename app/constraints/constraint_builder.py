from __future__ import annotations

from collections import defaultdict
from typing import Any


EMPTY_CONSTRAINTS = {
    "confirmed": [],
    "candidate": [],
    "conflicted": [],
    "missing": [],
    "forbidden_claims": [],
}


STATUS_PRIORITY = {
    "confirmed": 2,
    "candidate": 1,
}


def _normalize_value(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        normalized = value.strip()
        return normalized or None
    return str(value)


def _merge_constraint_source(
    grouped: dict[str, dict[str, str]],
    *,
    field: Any,
    value: Any,
    status: Any,
) -> None:
    normalized_field = _normalize_value(field)
    normalized_value = _normalize_value(value)
    normalized_status = _normalize_value(status) or "candidate"
    if normalized_status not in STATUS_PRIORITY:
        normalized_status = "candidate"
    if not normalized_field or not normalized_value:
        return

    field_values = grouped[normalized_field]
    existing_status = field_values.get(normalized_value)
    if existing_status is None or STATUS_PRIORITY[normalized_status] > STATUS_PRIORITY[existing_status]:
        field_values[normalized_value] = normalized_status


def build_constraints(
    stored_constraints: list[dict[str, Any]] | None,
    new_memories: list[dict[str, Any]] | None,
    memory_hits: list[dict[str, Any]] | None,
    required_fields: list[str] | None,
) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, dict[str, str]] = defaultdict(dict)

    for item in stored_constraints or []:
        _merge_constraint_source(
            grouped,
            field=item.get("constraint_key") or item.get("key"),
            value=item.get("constraint_value") or item.get("value"),
            status=item.get("status"),
        )

    for item in new_memories or []:
        payload = item.get("memory_payload") or {}
        _merge_constraint_source(
            grouped,
            field=payload.get("field"),
            value=payload.get("value"),
            status=payload.get("status"),
        )

    for item in memory_hits or []:
        payload = item.get("memory_payload") or {}
        _merge_constraint_source(
            grouped,
            field=payload.get("field"),
            value=payload.get("value"),
            status=payload.get("status"),
        )

    result = {key: value[:] for key, value in EMPTY_CONSTRAINTS.items()}

    for field, values in grouped.items():
        distinct_values = list(values.keys())
        if len(distinct_values) > 1:
            result["conflicted"].append({"key": field, "values": distinct_values})
            continue

        value = distinct_values[0]
        status = values[value]
        result[status].append({"key": field, "value": value})

    present_fields = set(grouped.keys())
    for field in required_fields or []:
        normalized_field = _normalize_value(field)
        if normalized_field and normalized_field not in present_fields:
            result["missing"].append({"key": normalized_field, "reason": "required_for_reply"})

    return result
