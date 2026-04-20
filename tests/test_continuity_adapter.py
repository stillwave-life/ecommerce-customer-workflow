from __future__ import annotations

from app import continuity_adapter


class CompressRecorder:
    def __init__(self) -> None:
        self.called = False

    def compress_context(self, history: list[dict], config: dict) -> dict:
        self.called = True
        return {
            "compressed": True,
            "compressed_history": [{"role": "system", "content": "compressed"}],
            "original_turns": len(history),
            "compressed_turns": 1,
        }

    def load_config(self) -> dict:
        return {}


def test_long_message_content_triggers_compression(monkeypatch) -> None:
    recorder = CompressRecorder()
    monkeypatch.setattr(continuity_adapter, "_load_continuity_module", lambda: recorder)
    history = [{"role": "user", "content": "长内容" * 200} for _ in range(16)]

    result = continuity_adapter.check_and_compress_context(history, max_tokens=1_000)

    assert result["compressed"] is True
    assert result["history"] == [{"role": "system", "content": "compressed"}]
    assert recorder.called is True


def test_token_estimate_uses_message_content_length() -> None:
    short_history = [{"role": "user", "content": "ok"} for _ in range(100)]
    long_history = [{"role": "user", "content": "长内容" * 200} for _ in range(16)]

    short_estimate = continuity_adapter.estimate_history_tokens(short_history)
    long_estimate = continuity_adapter.estimate_history_tokens(long_history)

    assert short_estimate < 65_000
    assert long_estimate > 650


def test_missing_continuity_returns_original_history(monkeypatch) -> None:
    monkeypatch.setattr(continuity_adapter, "_load_continuity_module", lambda: None)
    history = [{"role": "user", "content": "长内容" * 200} for _ in range(16)]

    result = continuity_adapter.check_and_compress_context(history, max_tokens=1_000)

    assert result["compressed"] is False
    assert result["history"] == history
    assert result["message"] == "Continuity not available, skipping compression"
