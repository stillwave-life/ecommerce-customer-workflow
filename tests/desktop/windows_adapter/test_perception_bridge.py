from app.desktop.perception.jd_workspace_parser import parse_jd_workspace
from app.desktop.perception.region_classifier import classify_regions
from app.desktop.windows_adapter.foreground_window import build_foreground_window_result
from app.desktop.windows_adapter.input_focus import build_focus_result
from app.desktop.windows_adapter.perception_bridge import build_windows_perception_result


def test_build_windows_perception_result_keeps_desktop_context_and_focus_result():
    probe_result = build_foreground_window_result(
        handle=1001,
        title="evw10158991",
        process_name="jd-workbench.exe",
        bounds=[0, 0, 1680, 1048],
        is_foreground=True,
    )
    regions = classify_regions([
        {"region_hint": "chat", "text": "这款还有吗？", "message_role": "customer"},
        {"region_hint": "input", "editable": True, "has_smart_reply": True, "existing_text": ""},
        {"region_hint": "send_button", "visible": True},
    ])["regions"]
    desktop_context = parse_jd_workspace(
        regions,
        active_customer={"id": "jd_4a3d4c80e30ef", "name": "jd_4a3d4c80e30ef"},
        confidence=0.9,
    )
    focus_result = build_focus_result(
        focused=True,
        target_role="edit",
        target_name="输入框",
        reason="",
    )

    result = build_windows_perception_result(
        probe_result=probe_result,
        desktop_context=desktop_context,
        focus_result=focus_result,
    )

    assert result["ok"] is True
    assert result["probe_result"]["handle"] == 1001
    assert result["desktop_context"]["platform"] == "jd_customer_service"
    assert result["focus_result"]["focused"] is True
