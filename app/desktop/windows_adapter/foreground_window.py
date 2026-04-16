from __future__ import annotations


def build_foreground_window_result(
    *,
    handle: int,
    title: str,
    process_name: str,
    bounds: list[int],
    is_foreground: bool,
) -> dict:
    return {
        "ok": True,
        "handle": handle,
        "title": title,
        "process_name": process_name,
        "bounds": list(bounds),
        "is_foreground": is_foreground,
    }
