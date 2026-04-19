from __future__ import annotations

from importlib.util import find_spec
from typing import Any

from app.desktop.windows_adapter.ui_node_adapter import build_windows_node


if find_spec("pywinauto") is None:
    raise ImportError("pywinauto with uia backend is not available")

MAX_UIA_DEPTH = 3
CLICKABLE_CONTROL_TYPES = {"button", "hyperlink", "menuitem", "listitem", "tabitem"}
EDITABLE_CONTROL_TYPES = {"edit", "document"}


def _bounds_from_rectangle(rectangle: Any) -> list[int]:
    if rectangle is None:
        return [0, 0, 0, 0]
    return [int(rectangle.left), int(rectangle.top), int(rectangle.right), int(rectangle.bottom)]


def _safe_call(obj: Any, attr: str) -> Any:
    value = getattr(obj, attr, None)
    if callable(value):
        try:
            return value()
        except Exception:
            return None
    return value


def _control_value(control: Any, element_info: Any) -> str:
    value = _safe_call(control, "get_value")
    if value:
        return str(value)
    legacy_value = getattr(element_info, "value", None)
    if legacy_value:
        return str(legacy_value)
    return ""


def _control_text(control: Any, element_info: Any) -> str:
    for attr in ("rich_text", "texts"):
        value = getattr(control, attr, None)
        if callable(value):
            try:
                result = value()
            except Exception:
                continue
            if isinstance(result, list):
                joined = " ".join(str(item) for item in result if str(item).strip())
                if joined:
                    return joined
            elif result:
                return str(result)
    value_text = _control_value(control, element_info)
    if value_text:
        return value_text
    return str(getattr(element_info, "name", "") or "")


def _is_editable(control_type: str, enabled: bool, value: str, class_name: str) -> bool:
    normalized_type = control_type.lower()
    normalized_class = class_name.lower()
    return enabled and (normalized_type in EDITABLE_CONTROL_TYPES or bool(value) or "edit" in normalized_class)


def _is_clickable(control_type: str, enabled: bool) -> bool:
    return enabled and control_type.lower() in CLICKABLE_CONTROL_TYPES


def _should_keep_node(node: dict[str, Any]) -> bool:
    if node.get("children"):
        return True
    if node.get("visible") and (node.get("editable") or node.get("clickable")):
        return True
    if str(node.get("text", "")).strip():
        return True
    if str(node.get("value", "")).strip():
        return True
    if str(node.get("name", "")).strip() and node.get("visible", True):
        return True
    return False


def _node_from_control(control: Any, path: list[str], parent_role: str, depth: int) -> dict[str, Any]:
    element_info = getattr(control, "element_info", None)
    control_type = str(getattr(element_info, "control_type", "") or "")
    name = str(getattr(element_info, "name", "") or "")
    automation_id = str(getattr(element_info, "automation_id", "") or "")
    class_name = str(getattr(element_info, "class_name", "") or "")
    rectangle = getattr(element_info, "rectangle", None)
    enabled = bool(getattr(element_info, "enabled", True))
    visible = bool(getattr(element_info, "visible", True))
    role = control_type.lower() or "unknown"
    value = _control_value(control, element_info)

    node = build_windows_node(
        role=role,
        name=name,
        text=_control_text(control, element_info),
        bounds=_bounds_from_rectangle(rectangle),
        editable=_is_editable(control_type, enabled, value, class_name),
        clickable=_is_clickable(control_type, enabled),
        visible=visible,
        automation_id=automation_id,
        control_type=control_type,
        class_name=class_name,
        value=value,
        enabled=enabled,
        parent_role=parent_role,
        path=path + [role],
    )
    node["children"] = _child_nodes(control, path + [role], role, depth + 1)
    return node


def _child_nodes(control: Any, path: list[str], parent_role: str, depth: int) -> list[dict[str, Any]]:
    if depth >= MAX_UIA_DEPTH:
        return []
    children = getattr(control, "children", None)
    if not callable(children):
        return []
    try:
        child_controls = children()
    except Exception:
        return []
    return [node for child in child_controls if (node := _node_from_control(child, path, parent_role, depth)) and _should_keep_node(node)]


def _first_level_nodes(active: Any) -> list[dict[str, Any]]:
    children = getattr(active, "children", None)
    if not callable(children):
        return []
    try:
        child_controls = children()
    except Exception:
        return []
    return [node for child in child_controls if (node := _node_from_control(child, ["window"], "window", 0)) and _should_keep_node(node)]


def collect_snapshot() -> dict[str, Any]:
    from pywinauto import Desktop

    desktop = Desktop(backend="uia")
    active = desktop.get_active()
    element_info = getattr(active, "element_info", None)
    rectangle = getattr(element_info, "rectangle", None)

    handle = getattr(element_info, "handle", 0) or 0
    process_id = getattr(element_info, "process_id", None)
    process_name = f"pid:{process_id}" if process_id is not None else ""

    window = {
        "handle": int(handle),
        "title": active.window_text(),
        "process_name": process_name,
        "bounds": _bounds_from_rectangle(rectangle),
        "is_foreground": True,
    }

    return {
        "window": window,
        "nodes": _first_level_nodes(active),
    }
