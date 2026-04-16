from app.desktop.launcher import launch_desktop_assistant
from app.desktop.perception.jd_workspace_parser import parse_jd_workspace
from app.desktop.perception.region_classifier import classify_regions
from app.desktop.windows_uia_foundation.action_gate import build_action_gate_result
from app.desktop.windows_uia_foundation.diagnostics_report import build_diagnostics_report
from app.desktop.windows_uia_foundation.focus_verifier import build_focus_verification
from app.desktop.windows_uia_foundation.input_candidate_ranker import rank_input_candidates
from app.desktop.windows_uia_foundation.probe_diagnostics import build_probe_diagnostics


def test_uia_foundation_pipeline_preserves_manual_send_boundary():
    nodes = [
        {"role": "edit", "name": "输入框", "bounds": [360, 690, 970, 1010], "editable": True, "clickable": True, "visible": True, "region_hint": "input", "has_smart_reply": True, "existing_text": ""},
        {"role": "text", "name": "客户消息", "text": "这款还有吗？", "region_hint": "chat", "message_role": "customer"},
        {"role": "button", "name": "发送(F1)", "visible": True, "region_hint": "send_button"},
    ]

    probe = build_probe_diagnostics(
        window={"title": "evw10158991", "handle": 1001},
        node_count=3,
        editable_node_count=1,
        clickable_node_count=2,
        visible_node_count=3,
    )
    ranked = rank_input_candidates(nodes)
    gate = build_action_gate_result(score=ranked["candidates"][0]["score"], candidate_count=len(ranked["candidates"]))
    focus = build_focus_verification(focused=True, target_name="输入框")
    regions = classify_regions(nodes)["regions"]
    desktop_context = parse_jd_workspace(
        regions,
        active_customer={"id": "jd_4a3d4c80e30ef", "name": "jd_4a3d4c80e30ef"},
        confidence=0.9,
    )
    report = build_diagnostics_report(
        window=probe["window"],
        node_stats=probe["node_stats"],
        input_candidates=ranked["candidates"],
        gate_result=gate,
        focus_result=focus,
        desktop_context=desktop_context,
    )

    launch_result = launch_desktop_assistant(
        command="京东客服启动",
        desktop_context=report["desktop_context"],
        shop_id="shop_001",
        session_id="desktop-session-1",
    )

    assert launch_result["ok"] is True
    assert gate["decision"] == "allow_focus"
    assert focus["focused"] is True
    assert launch_result["fill_action"]["auto_send_allowed"] is False
    assert launch_result["fill_action"]["send_policy"] == "manual_only"
