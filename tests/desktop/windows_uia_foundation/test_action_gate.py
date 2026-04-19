from app.desktop.windows_uia_foundation.action_gate import build_action_gate_result


def test_build_action_gate_result_allows_focus_for_high_score():
    result = build_action_gate_result(score=0.86, candidate_count=1)

    assert result["decision"] == "allow_focus"
    assert result["reason"] == "candidate_score_high_enough"


def test_build_action_gate_result_blocks_when_no_candidates():
    result = build_action_gate_result(score=0.0, candidate_count=0)

    assert result["decision"] == "block"
    assert result["reason"] == "no_input_candidates"


def test_build_action_gate_result_requests_manual_review_for_mid_score():
    result = build_action_gate_result(score=0.62, candidate_count=1)

    assert result["decision"] == "manual_review"
    assert result["reason"] == "candidate_score_uncertain"


def test_build_action_gate_result_blocks_fill_when_focus_not_allowed():
    result = build_action_gate_result(score=0.49, candidate_count=1)

    assert result["decision"] == "block"
    assert result["reason"] == "candidate_score_too_low"
