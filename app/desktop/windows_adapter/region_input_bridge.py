from __future__ import annotations

from typing import Any


def _path_text(node: dict[str, Any]) -> str:
    path = node.get("path") or []
    return " ".join(str(item).lower() for item in path)


def _infer_region_hint(node: dict[str, Any]) -> str:
    existing = str(node.get("region_hint", "")).strip()
    if existing:
        return existing

    role = str(node.get("role", "")).lower()
    control_type = str(node.get("control_type", "")).lower()
    automation_id = str(node.get("automation_id", "")).lower()
    name = str(node.get("name", "")).lower()
    text = str(node.get("text", "")).lower()
    path_text = _path_text(node)

    if "send" in automation_id or "send_button" in path_text or "发送" in name or "发送" in text:
        return "send_button"
    if node.get("editable") or role == "edit" or control_type == "edit" or "reply_editor" in path_text:
        return "input"
    if "chat" in path_text or "message" in path_text or "客户消息" in name or "这款" in text:
        return "chat"
    if "product" in path_text or any(keyword in name for keyword in ("商品", "sku")):
        return "product"
    if "user" in path_text or "order" in path_text or any(keyword in name for keyword in ("订单", "用户")):
        return "user_order"
    if "conversation" in path_text or "session" in path_text:
        return "conversation_list"
    return ""


def _augment_node(node: dict[str, Any]) -> dict[str, Any]:
    result = node.copy()
    result["children"] = [child.copy() for child in result.get("children", []) if isinstance(child, dict)]
    region_hint = _infer_region_hint(result)
    if region_hint:
        result["region_hint"] = region_hint

    if region_hint == "chat" and not result.get("message_role"):
        result["message_role"] = "customer"
    if region_hint == "input":
        result.setdefault("existing_text", str(result.get("value", result.get("text", "")) or ""))
        result.setdefault("has_smart_reply", False)
    if region_hint == "send_button":
        result["visible"] = bool(result.get("visible", True))
    return result


def _flatten_nodes(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    flattened: list[dict[str, Any]] = []
    for node in nodes:
        flattened.append(node)
        children = node.get("children") or []
        child_nodes = [child for child in children if isinstance(child, dict)]
        flattened.extend(_flatten_nodes(child_nodes))
    return flattened


def build_region_input_nodes(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [_augment_node(node) for node in _flatten_nodes(nodes)]
