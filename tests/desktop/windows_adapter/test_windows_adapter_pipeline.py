from app.desktop.launcher import launch_desktop_assistant
from app.desktop.perception.jd_workspace_parser import parse_jd_workspace
from app.desktop.perception.region_classifier import classify_regions
from app.desktop.windows_adapter.foreground_window import build_foreground_window_result
from app.desktop.windows_adapter.input_focus import build_focus_result
from app.desktop.windows_adapter.perception_bridge import build_windows_perception_result


def test_windows_adapter_pipeline_keeps_manual_send_boundary():
    probe_result = build_foreground_window_result(
        handle=1001,
        title="evw10158991",
        process_name="jd-workbench.exe",
        bounds=[0, 0, 1680, 1048],
        is_foreground=True,
    )
    regions = classify_regions([
        {"region_hint": "chat", "text": "这款还有吗？", "message_role": "customer"},
        {"region_hint": "product", "title": "台式电脑主机", "sku": "10017775551", "stock_status": "无货"},
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
    bridge_result = build_windows_perception_result(
        probe_result=probe_result,
        desktop_context=desktop_context,
        focus_result=focus_result,
    )

    launch_result = launch_desktop_assistant(
        command="京东客服启动",
        desktop_context=bridge_result["desktop_context"],
        shop_id="shop_001",
        session_id="desktop-session-1",
    )

    assert launch_result["ok"] is True
    assert bridge_result["focus_result"]["focused"] is True
    assert launch_result["fill_action"]["auto_send_allowed"] is False
    assert launch_result["fill_action"]["send_policy"] == "manual_only"
