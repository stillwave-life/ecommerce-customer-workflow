from app.desktop.context import (
    build_chat_context,
    build_desktop_context,
    build_input_context,
    build_product_context,
    build_user_order_context,
)


def test_build_desktop_context_defaults_to_safe_empty_values():
    context = build_desktop_context()

    assert context["platform"] == "unknown"
    assert context["confidence"] == 0.0
    assert context["chat_context"]["latest_customer_message"] == ""
    assert context["chat_context"]["contains_image"] is False
    assert context["product_context"]["items"] == []
    assert context["user_order_context"]["orders"] == []
    assert context["input_context"]["editable"] is False
    assert context["input_context"]["send_button_visible"] is False


def test_build_desktop_context_preserves_visible_jd_context():
    context = build_desktop_context(
        platform="jd_customer_service",
        confidence=0.86,
        active_customer={"id": "jd_4a3d4c80e30ef", "name": "jd_4a3d4c80e30ef"},
        chat_context=build_chat_context(
            latest_customer_message="这款还有吗？",
            recent_messages=[{"role": "customer", "text": "这款还有吗？"}],
            contains_image=True,
        ),
        product_context=build_product_context(
            tab_active=True,
            items=[{"title": "台式电脑主机", "sku": "10017775551", "stock_status": "无货"}],
        ),
        user_order_context=build_user_order_context(
            user_labels=["PLUS"],
            orders=[{"status": "近三个月无订单"}],
            service_forms=[],
        ),
        input_context=build_input_context(
            editable=True,
            has_smart_reply=True,
            send_button_visible=True,
            existing_text="",
        ),
    )

    assert context["platform"] == "jd_customer_service"
    assert context["active_customer"]["id"] == "jd_4a3d4c80e30ef"
    assert context["chat_context"]["latest_customer_message"] == "这款还有吗？"
    assert context["product_context"]["items"][0]["sku"] == "10017775551"
    assert context["input_context"]["editable"] is True


def test_build_desktop_context_copies_active_customer():
    active_customer = {"id": "jd_4a3d4c80e30ef", "name": "原始名称"}

    context = build_desktop_context(active_customer=active_customer)
    active_customer["name"] = "已被外部修改"

    assert context["active_customer"]["name"] == "原始名称"
