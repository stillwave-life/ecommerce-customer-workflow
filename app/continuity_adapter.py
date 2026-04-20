from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

DEFAULT_MAX_TOKENS = 200_000
COMPRESSION_THRESHOLD = 0.65
MIN_TURNS_TO_COMPRESS = 15
CHARS_PER_TOKEN = 4
CONTINUITY_PATHS = (
    Path.home() / ".openclaw" / "skills" / "Continuity" / "scripts" / "auto_compress.py",
    Path.home() / ".openclaw" / "workspace" / "skills" / "Continuity" / "scripts" / "auto_compress.py",
)


def _load_continuity_module() -> Any | None:
    for module_path in CONTINUITY_PATHS:
        spec = importlib.util.spec_from_file_location("openclaw_continuity_auto_compress", module_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            try:
                spec.loader.exec_module(module)
            except FileNotFoundError:
                continue
            return module
    return None


def _stringify_content(content: Any) -> str:
    if isinstance(content, str):
        return content
    if content is None:
        return ""
    return json.dumps(content, ensure_ascii=False, separators=(",", ":"))


def estimate_history_tokens(history: list[dict[str, Any]]) -> int:
    total_chars = 0
    for message in history:
        if not isinstance(message, dict):
            total_chars += len(_stringify_content(message))
            continue
        total_chars += len(_stringify_content(message.get("role")))
        total_chars += len(_stringify_content(message.get("content")))
    return max(1, (total_chars + CHARS_PER_TOKEN - 1) // CHARS_PER_TOKEN)


def check_and_compress_context(history: list[dict[str, Any]], max_tokens: int = DEFAULT_MAX_TOKENS) -> dict[str, Any]:
    continuity = _load_continuity_module()
    if continuity is None:
        return {
            "compressed": False,
            "history": history,
            "message": "Continuity not available, skipping compression",
        }

    usage_percent = estimate_history_tokens(history) / max_tokens
    if usage_percent <= COMPRESSION_THRESHOLD or len(history) <= MIN_TURNS_TO_COMPRESS:
        return {
            "compressed": False,
            "history": history,
            "message": f"Usage: {usage_percent:.1%}, no compression needed",
        }

    result = continuity.compress_context(history, continuity.load_config())
    if not result.get("compressed"):
        return {
            "compressed": False,
            "history": history,
            "message": f"Usage: {usage_percent:.1%}, compression skipped",
        }

    return {
        "compressed": True,
        "history": result["compressed_history"],
        "original_turns": result["original_turns"],
        "compressed_turns": result["compressed_turns"],
        "message": "Context compressed successfully",
    }


if __name__ == "__main__":
    history = [{"role": "user", "content": f"Message {i}"} for i in range(20)]
    result = check_and_compress_context(history)
    print(json.dumps(result, ensure_ascii=False, indent=2))
