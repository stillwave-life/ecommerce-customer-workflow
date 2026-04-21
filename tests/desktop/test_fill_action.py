from app.desktop.fill_action import DEFAULT_INPUT_BOUNDS, build_fill_action


def test_build_fill_action_requires_manual_send():
    action = build_fill_action("您好，这款需要再确认库存。", target="reply_box")

    assert action["ok"] is True
    assert action["action"] == "fill_input"
    assert action["target"] == "reply_box"
    assert action["text"] == "您好，这款需要再确认库存。"
    assert action["send_policy"] == "manual_only"
    assert action["ready_for_manual_send"] is True
    assert action["auto_send_allowed"] is False
    assert action["targeting_strategy"] == "coordinates"
    assert action["paste_via_clipboard"] is True
    assert action["clear_before_fill"] is True
    assert action["verify_mode"] == "screenshot_diff_required"
    assert action["target_bounds"] == DEFAULT_INPUT_BOUNDS


def test_build_fill_action_rejects_empty_text():
    action = build_fill_action("", target="reply_box")

    assert action["ok"] is False
    assert action["error"] == "reply text is required"
    assert action["auto_send_allowed"] is False


def test_build_fill_action_keeps_focus_target_metadata():
    action = build_fill_action(
        "您好，这款需要再确认库存。",
        target="reply_box",
        target_bounds=[360, 690, 970, 1010],
        target_automation_id="reply-editor",
        verify_mode="readback_required",
    )

    assert action["target_bounds"] == [360, 690, 970, 1010]
    assert action["target_automation_id"] == "reply-editor"
    assert action["verify_mode"] == "readback_required"
