from app.desktop.fill_action import build_fill_action


def test_build_fill_action_requires_manual_send():
    action = build_fill_action("您好，这款需要再确认库存。", target="reply_box")

    assert action["ok"] is True
    assert action["action"] == "fill_input"
    assert action["target"] == "reply_box"
    assert action["text"] == "您好，这款需要再确认库存。"
    assert action["send_policy"] == "manual_only"
    assert action["ready_for_manual_send"] is True
    assert action["auto_send_allowed"] is False


def test_build_fill_action_rejects_empty_text():
    action = build_fill_action("", target="reply_box")

    assert action["ok"] is False
    assert action["error"] == "reply text is required"
    assert action["auto_send_allowed"] is False
