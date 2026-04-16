from app.desktop.context import (
    build_chat_context,
    build_desktop_context,
    build_input_context,
    build_product_context,
    build_user_order_context,
)
from app.desktop.prepare_mapper import build_prepared_from_desktop_context


def test_build_prepared_from_desktop_context_maps_chat_and_product():
    desktop_context = build_desktop_context(
        platform="jd_customer_service",
        confidence=0.9,
        active_customer={"id": "jd_4a3d4c80e30ef", "name": "jd_4a3d4c80e30ef"},
        chat_context=build_chat_context(
            latest_customer_message="这款还有吗？",
            recent_messages=[{"role": "customer", "text": "这款还有吗？"}],
            contains_image=False,
        ),
        product_context=build_product_context(
            tab_active=True,
            items=[{"title": "台式电脑主机", "sku": "10017775551", "stock_status": "无货"}],
        ),
        user_order_context=build_user_order_context(user_labels=["PLUS"]),
        input_context=build_input_context(editable=True, send_button_visible=True),
    )

    prepared = build_prepared_from_desktop_context(
        desktop_context,
        shop_id="jd-default",
        session_id="desktop-session-1",
    )

    assert prepared["shop_id"] == "jd-default"
    assert prepared["session_id"] == "desktop-session-1"
    assert prepared["source_type"] == "text"
    assert prepared["source_value"] == "这款还有吗？"
    assert prepared["user_message"] == "这款还有吗？"
    assert prepared["product_ref"] == {"type": "sku", "value": "10017775551"}
    assert prepared["page_context"]["platform"] == "jd_customer_service"
    assert prepared["page_context"]["active_customer"]["id"] == "jd_4a3d4c80e30ef"
    assert prepared["parsed_entities"][0] == {"type": "sku", "value": "10017775551", "source": "desktop_product_context"}


def test_build_prepared_from_desktop_context_uses_clarification_strategy_without_message():
    desktop_context = build_desktop_context(platform="jd_customer_service", confidence=0.8)

    prepared = build_prepared_from_desktop_context(
        desktop_context,
        shop_id="jd-default",
        session_id="desktop-session-1",
    )

    assert prepared["user_message"] == ""
    assert prepared["reply_strategy"] == "ask_for_clarification"
    assert prepared["constraints"]["missing"][0]["key"] == "customer_message"
