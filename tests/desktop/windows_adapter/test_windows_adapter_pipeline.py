from app.desktop.launcher import launch_desktop_assistant
from app.desktop.perception.jd_workspace_parser import parse_jd_workspace
from app.desktop.perception.region_classifier import classify_regions
from app.desktop.windows_adapter.foreground_window import build_foreground_window_result
from app.desktop.windows_adapter.input_focus import build_focus_result
from app.desktop.windows_adapter.perception_bridge import build_windows_perception_result
from app.desktop.windows_adapter.region_input_bridge import build_region_input_nodes
from app.desktop.windows_adapter.ui_node_adapter import build_windows_node


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


def test_windows_adapter_pipeline_accepts_uia_style_nodes():
    probe_result = build_foreground_window_result(
        handle=1001,
        title="evw10158991",
        process_name="jd-workbench.exe",
        bounds=[0, 0, 1680, 1048],
        is_foreground=True,
    )
    nodes = build_region_input_nodes([
        build_windows_node(
            role="text",
            name="客户消息",
            text="这款还有吗？",
            bounds=[380, 320, 900, 420],
            editable=False,
            clickable=False,
            visible=True,
            control_type="Text",
            class_name="TextBlock",
            parent_role="list",
            path=["window", "chat_panel", "message_list"],
        ),
        build_windows_node(
            role="text",
            name="商品信息",
            text="",
            bounds=[1120, 240, 1540, 460],
            editable=False,
            clickable=False,
            visible=True,
            control_type="Text",
            class_name="TextBlock",
            parent_role="pane",
            path=["window", "product_panel"],
        ) | {"title": "台式电脑主机", "sku": "10017775551", "stock_status": "无货"},
        build_windows_node(
            role="edit",
            name="输入框",
            text="",
            bounds=[360, 690, 970, 1010],
            editable=True,
            clickable=True,
            visible=True,
            automation_id="reply-editor",
            control_type="Edit",
            class_name="RichEdit",
            enabled=True,
            parent_role="pane",
            path=["window", "footer", "reply_editor"],
        ),
        build_windows_node(
            role="button",
            name="发送(F1)",
            text="发送(F1)",
            bounds=[1200, 920, 1320, 980],
            editable=False,
            clickable=True,
            visible=True,
            automation_id="send-btn",
            control_type="Button",
            class_name="Button",
            enabled=True,
            parent_role="pane",
            path=["window", "footer", "send_button"],
        ),
    ])
    regions = classify_regions(nodes)["regions"]
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
    assert desktop_context["chat_context"]["latest_customer_message"] == "这款还有吗？"
    assert desktop_context["product_context"]["items"][0]["sku"] == "10017775551"
    assert launch_result["fill_action"]["auto_send_allowed"] is False


def test_windows_adapter_pipeline_accepts_recursive_provider_nodes():
    probe_result = build_foreground_window_result(
        handle=1001,
        title="evw10158991",
        process_name="jd-workbench.exe",
        bounds=[0, 0, 1680, 1048],
        is_foreground=True,
    )
    nodes = build_region_input_nodes([
        {
            "role": "pane",
            "name": "聊天区",
            "text": "",
            "bounds": [300, 200, 1000, 780],
            "editable": False,
            "clickable": False,
            "visible": True,
            "control_type": "Pane",
            "path": ["window", "pane"],
            "children": [
                {
                    "role": "text",
                    "name": "客户消息",
                    "text": "这款还有吗？",
                    "bounds": [380, 320, 900, 420],
                    "editable": False,
                    "clickable": False,
                    "visible": True,
                    "control_type": "Text",
                    "path": ["window", "pane", "text"],
                    "children": [],
                }
            ],
        },
        {
            "role": "edit",
            "name": "输入框",
            "text": "",
            "value": "已有草稿",
            "bounds": [360, 690, 970, 1010],
            "editable": True,
            "clickable": False,
            "visible": True,
            "control_type": "Edit",
            "class_name": "RichEdit",
            "enabled": True,
            "path": ["window", "edit"],
            "children": [],
        },
    ])
    regions = classify_regions(nodes)["regions"]
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
    assert desktop_context["chat_context"]["latest_customer_message"] == "这款还有吗？"
    assert desktop_context["input_context"]["existing_text"] == "已有草稿"
