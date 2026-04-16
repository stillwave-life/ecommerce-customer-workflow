from app.desktop.launcher import launch_desktop_assistant
from app.desktop.perception.jd_workspace_parser import parse_jd_workspace


def test_perception_pipeline_outputs_launcher_consumable_desktop_context():
    regions = {
        "chat_region": [{"text": "这款还有吗？", "message_role": "customer"}],
        "product_region": [{"title": "台式电脑主机", "sku": "10017775551", "stock_status": "无货"}],
        "user_order_region": [{"label": "PLUS"}],
        "input_region": [{"editable": True, "has_smart_reply": True, "existing_text": ""}],
        "send_button_region": [{"visible": True}],
        "conversation_list_region": [],
    }

    desktop_context = parse_jd_workspace(
        regions,
        active_customer={"id": "jd_4a3d4c80e30ef", "name": "jd_4a3d4c80e30ef"},
        confidence=0.9,
    )

    result = launch_desktop_assistant(
        command="京东客服启动",
        desktop_context=desktop_context,
        shop_id="shop_001",
        session_id="desktop-session-1",
    )

    assert result["ok"] is True
    assert result["reply"]["prepared"]["product_ref"] == {"type": "sku", "value": "10017775551"}
    assert result["fill_action"]["send_policy"] == "manual_only"
