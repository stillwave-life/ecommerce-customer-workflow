from __future__ import annotations

from collections.abc import Callable
from typing import Any


BackendImporter = Callable[[], Any]


def _default_importer() -> Any:
    try:
        from app.desktop.windows_adapter import pywinauto_fill_impl
    except Exception as exc:
        raise ImportError("pywinauto fill backend dependency not installed") from exc
    return pywinauto_fill_impl


def provider_available(importer: BackendImporter | None = None) -> bool:
    importer = importer or _default_importer
    try:
        importer()
    except Exception:
        return False
    return True


def build_fill_provider(importer: BackendImporter | None = None):
    importer = importer or _default_importer
    backend_module = importer()
    provider = getattr(backend_module, "fill_text", None)
    if not callable(provider):
        raise RuntimeError("pywinauto_fill_provider_missing_fill_text")
    return provider
