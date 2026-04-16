from app.desktop.context import build_chat_context, build_desktop_context, build_input_context, build_product_context
from app.desktop.reply_composer import compose_desktop_reply


def test_compose_desktop_reply_returns_prepared_and_reply_draft():
    desktop_context = build_desktop_context(
        platform="jd_customer_service",
        confidence=0.92,
        chat_context=build_chat_context(latest_customer_message="这款还有吗？"),
        product_context=build_product_context(items=[{"title": "黑色外套", "sku": "SKU001"}]),
        input_context=build_input_context(editable=True, send_button_visible=True),
    )

    result = compose_desktop_reply(
        desktop_context,
        shop_id="shop_001",
        session_id="desktop-session-1",
    )

    assert result["ok"] is True
    assert result["prepared"]["user_message"] == "这款还有吗？"
    assert result["reply_draft"]
    assert "facts_used" in result
    assert result["next_action"] == "fill_input"


def test_compose_desktop_reply_blocks_fill_when_input_not_editable():
    desktop_context = build_desktop_context(
        platform="jd_customer_service",
        confidence=0.92,
        chat_context=build_chat_context(latest_customer_message="这款还有吗？"),
        input_context=build_input_context(editable=False, send_button_visible=True),
    )

    result = compose_desktop_reply(
        desktop_context,
        shop_id="shop_001",
        session_id="desktop-session-1",
    )

    assert result["ok"] is True
    assert result["next_action"] == "manual_review"
    assert result["safety"]["can_fill_input"] is False
