from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.reply.reply_builder import build_reply_draft


def test_build_reply_draft_asks_for_clarification_when_constraints_missing() -> None:
    prepared = {
        "user_message": "这个怎么样",
        "knowledge_hits": {"catalog": [], "faq": [], "rules": []},
        "memory_hits": [{"memory_text": "客户之前问过256G版本"}],
        "constraints": {
            "confirmed": [],
            "candidate": [],
            "conflicted": [],
            "missing": [{"key": "product_id", "reason": "required_for_reply"}],
            "forbidden_claims": [],
        },
        "reply_strategy": "ask_for_clarification",
    }

    result = build_reply_draft(prepared)

    assert "补充" in result["reply_draft"] or "确认" in result["reply_draft"]
    assert result["facts_used"] == []


def test_build_reply_draft_resolves_conflict_from_constraints() -> None:
    prepared = {
        "user_message": "哪个更合适",
        "knowledge_hits": {"catalog": [], "faq": [], "rules": []},
        "memory_hits": [],
        "constraints": {
            "confirmed": [],
            "candidate": [],
            "conflicted": [{"key": "color", "values": ["黑色", "白色"]}],
            "missing": [],
            "forbidden_claims": [],
        },
        "reply_strategy": "resolve_conflict",
    }

    result = build_reply_draft(prepared)

    assert "黑色" in result["reply_draft"]
    assert "白色" in result["reply_draft"]
    assert "确认" in result["reply_draft"]


def test_build_reply_draft_answers_with_context_and_memory_hints() -> None:
    prepared = {
        "user_message": "这个怎么样",
        "knowledge_hits": {
            "catalog": [{"field": "颜色", "value": "黑色"}],
            "faq": [],
            "rules": [],
        },
        "memory_hits": [{"memory_text": "客户之前问过256G版本"}],
        "constraints": {
            "confirmed": [],
            "candidate": [],
            "conflicted": [],
            "missing": [],
            "forbidden_claims": [],
        },
        "reply_strategy": "answer_with_context",
    }

    result = build_reply_draft(prepared)

    assert "颜色：黑色" in result["reply_draft"]
    assert any("catalog:颜色" == item for item in result["facts_used"])
    assert any("memory:" in item for item in result["facts_used"])


if __name__ == "__main__":
    test_build_reply_draft_asks_for_clarification_when_constraints_missing()
    test_build_reply_draft_resolves_conflict_from_constraints()
    test_build_reply_draft_answers_with_context_and_memory_hints()
    print("ok")
