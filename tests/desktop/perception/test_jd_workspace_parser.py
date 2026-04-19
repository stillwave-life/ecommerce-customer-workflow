from app.desktop.perception.jd_workspace_parser import parse_jd_workspace


def test_parse_jd_workspace_builds_desktop_context_from_regions():
    regions = {
        "chat_region": [{"text": "这款还有吗？", "message_role": "customer"}],
        "product_region": [{"title": "台式电脑主机", "sku": "10017775551", "stock_status": "无货"}],
        "user_order_region": [{"label": "PLUS"}, {"order_summary": "近三个月无订单"}],
        "input_region": [{"editable": True, "has_smart_reply": True, "existing_text": ""}],
        "send_button_region": [{"visible": True}],
        "conversation_list_region": [],
    }

    result = parse_jd_workspace(
        regions,
        active_customer={"id": "jd_4a3d4c80e30ef", "name": "jd_4a3d4c80e30ef"},
        confidence=0.91,
    )

    assert result["platform"] == "jd_customer_service"
    assert result["active_customer"]["id"] == "jd_4a3d4c80e30ef"
    assert result["chat_context"]["latest_customer_message"] == "这款还有吗？"
    assert result["product_context"]["items"][0]["sku"] == "10017775551"
    assert result["user_order_context"]["user_labels"] == ["PLUS"]
    assert result["input_context"]["editable"] is True
    assert result["input_context"]["send_button_visible"] is True


def test_parse_jd_workspace_preserves_product_and_order_context_from_jd_regions():
    regions = {
        "chat_region": [{"text": "什么时候发货？", "message_role": "customer"}],
        "product_region": [{"title": "黑色外套", "sku": "SKU001", "stock_status": "有货"}],
        "user_order_region": [{"label": "PLUS"}, {"order_summary": "近三个月无订单"}],
        "input_region": [{"editable": True, "has_smart_reply": False, "existing_text": "已有草稿"}],
        "send_button_region": [{"visible": True}],
        "conversation_list_region": [],
    }

    result = parse_jd_workspace(
        regions,
        active_customer={"id": "jd_user_001", "name": "jd_user_001"},
        confidence=0.95,
    )

    assert result["product_context"]["tab_active"] is True
    assert result["product_context"]["items"][0]["title"] == "黑色外套"
    assert result["user_order_context"]["orders"][0]["summary"] == "近三个月无订单"
    assert result["input_context"]["existing_text"] == "已有草稿"
