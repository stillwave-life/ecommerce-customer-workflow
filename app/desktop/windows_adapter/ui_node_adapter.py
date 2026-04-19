from __future__ import annotations


def build_windows_node(
    *,
    role: str,
    name: str,
    text: str,
    bounds: list[int],
    editable: bool,
    clickable: bool,
    visible: bool,
    automation_id: str = "",
    control_type: str = "",
    class_name: str = "",
    value: str = "",
    enabled: bool = True,
    parent_role: str = "",
    path: list[str] | None = None,
) -> dict:
    return {
        "role": role,
        "name": name,
        "text": text,
        "bounds": list(bounds),
        "editable": editable,
        "clickable": clickable,
        "visible": visible,
        "automation_id": automation_id,
        "control_type": control_type,
        "class_name": class_name,
        "value": value,
        "enabled": enabled,
        "parent_role": parent_role,
        "path": list(path or []),
        "children": [],
    }
