from app.desktop.context import build_chat_context, build_desktop_context, build_input_context
from app.desktop.launcher import launch_desktop_assistant


def test_launch_desktop_assistant_composes_fill_action_for_jd_context():
    desktop_context = build_desktop_context(
        platform="jd_customer_service",
        confidence=0.9,
        chat_context=build_chat_context(latest_customer_message="这款还有吗？"),
        input_context=build_input_context(editable=True, send_button_visible=True),
    )

    result = launch_desktop_assistant(
        command="京东客服启动",
        desktop_context=desktop_context,
        shop_id="shop_001",
        session_id="desktop-session-1",
    )

    assert result["ok"] is True
    assert result["command"] == "京东客服启动"
    assert result["platform"] == "jd_customer_service"
    assert result["reply"]["reply_draft"]
    assert result["fill_action"]["action"] == "fill_input"
    assert result["fill_action"]["auto_send_allowed"] is False


def test_launch_desktop_assistant_rejects_non_jd_context():
    desktop_context = build_desktop_context(platform="unknown", confidence=0.2)

    result = launch_desktop_assistant(
        command="京东客服启动",
        desktop_context=desktop_context,
        shop_id="shop_001",
        session_id="desktop-session-1",
    )

    assert result["ok"] is False
    assert result["error"] == "current screen is not recognized as jd customer service workspace"
