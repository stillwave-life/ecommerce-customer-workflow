from __future__ import annotations

from importlib.util import find_spec
from typing import Any, Callable


DesktopFactory = Callable[[], Any]


def _default_desktop_factory() -> Any:
    if find_spec("pywinauto") is None:
        raise ImportError("pywinauto fill backend is not available")
    from pywinauto import Desktop

    return Desktop(backend="uia")


def _readback_text(control: Any) -> str:
    for attr in ("window_text", "texts"):
        value = getattr(control, attr, None)
        if callable(value):
            result = value()
            if isinstance(result, list):
                joined = " ".join(str(item) for item in result if str(item).strip())
                if joined:
                    return joined
            elif result:
                return str(result)
    return str(getattr(control, "value", "") or "")


def fill_text(action: dict[str, Any], desktop_factory: DesktopFactory | None = None) -> dict[str, Any]:
    desktop_factory = desktop_factory or _default_desktop_factory
    desktop = desktop_factory()

    target_automation_id = str(action.get("target_automation_id", "")).strip()
    target_name = str(action.get("target_name", "")).strip()
    text = str(action.get("text", ""))

    if target_automation_id:
        control = desktop.window(auto_id=target_automation_id)
    elif target_name:
        control = desktop.window(title=target_name)
    else:
        raise RuntimeError("fill_target_not_resolved")

    setter = getattr(control, "set_edit_text", None)
    if not callable(setter):
        raise RuntimeError("fill_target_not_editable")

    setter(text)
    return {
        "target_name": target_name,
        "written_text": _readback_text(control),
    }
