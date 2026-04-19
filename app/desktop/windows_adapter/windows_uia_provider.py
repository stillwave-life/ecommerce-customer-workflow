from __future__ import annotations

from collections.abc import Callable
from typing import Any

from app.desktop.windows_adapter.live_backend import collect_live_uia_snapshot


BackendImporter = Callable[[], Any]


def _default_importer() -> Any:
    try:
        from app.desktop.windows_adapter import pywinauto_uia_backend
    except Exception as exc:
        raise ImportError("windows uia backend dependency not installed") from exc
    return pywinauto_uia_backend


def provider_available(importer: BackendImporter | None = None) -> bool:
    importer = importer or _default_importer
    try:
        importer()
    except Exception:
        return False
    return True


def collect_windows_uia_snapshot(importer: BackendImporter | None = None) -> dict[str, Any]:
    importer = importer or _default_importer
    try:
        backend_module = importer()
    except Exception:
        return {
            "ok": False,
            "error": "windows_uia_import_failed",
            "backend": {"type": "windows_uia", "live": True},
        }

    provider = getattr(backend_module, "collect_snapshot", None)
    if not callable(provider):
        return {
            "ok": False,
            "error": "windows_uia_provider_missing_collect_snapshot",
            "backend": {"type": "windows_uia", "live": True},
        }

    try:
        return collect_live_uia_snapshot(provider=provider)
    except Exception:
        return {
            "ok": False,
            "error": "windows_uia_collect_failed",
            "backend": {"type": "windows_uia", "live": True},
        }
