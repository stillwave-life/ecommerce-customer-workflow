from app.desktop.perception.region_classifier import classify_regions


def test_classify_regions_splits_chat_product_user_input_nodes():
    nodes = [
        {"region_hint": "chat", "text": "这款还有吗？"},
        {"region_hint": "product", "text": "台式电脑主机"},
        {"region_hint": "user_order", "text": "近三个月订单"},
        {"region_hint": "input", "text": ""},
        {"region_hint": "send_button", "text": "发送(F1)"},
    ]

    result = classify_regions(nodes)

    assert result["ok"] is True
    assert len(result["regions"]["chat_region"]) == 1
    assert len(result["regions"]["product_region"]) == 1
    assert len(result["regions"]["user_order_region"]) == 1
    assert len(result["regions"]["input_region"]) == 1
    assert len(result["regions"]["send_button_region"]) == 1
