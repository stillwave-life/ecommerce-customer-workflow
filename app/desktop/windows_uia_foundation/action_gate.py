from __future__ import annotations


def build_action_gate_result(*, score: float, candidate_count: int) -> dict:
    if candidate_count == 0:
        return {"decision": "block", "reason": "no_input_candidates", "score": score}
    if score >= 0.8:
        return {"decision": "allow_focus", "reason": "candidate_score_high_enough", "score": score}
    if score >= 0.5:
        return {"decision": "manual_review", "reason": "candidate_score_uncertain", "score": score}
    return {"decision": "block", "reason": "candidate_score_too_low", "score": score}
