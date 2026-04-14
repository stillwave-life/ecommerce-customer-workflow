from app.models import build_prepared_result


def test_build_prepared_result_includes_memory_fields():
    prepared = build_prepared_result(
        shop_id="shop-1",
        session_id="session-1",
        source_type="text",
        source_value="这个怎么样",
        user_message="这个怎么样",
        memory_hits=[{"memory_type": "spec_fact", "memory_text": "客户提到256G"}],
        constraints={"confirmed": [], "candidate": [], "conflicted": [], "missing": [], "forbidden_claims": []},
        reply_strategy="ask_for_clarification",
    )

    assert prepared["memory_hits"][0]["memory_type"] == "spec_fact"
    assert prepared["constraints"]["missing"] == []
    assert prepared["reply_strategy"] == "ask_for_clarification"
