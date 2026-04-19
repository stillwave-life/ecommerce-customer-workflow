from app.desktop.monitor_once import build_monitor_once_result


def test_build_monitor_once_result_returns_idle_when_message_is_unchanged():
    probe_result = {
        "ok": True,
        "desktop_context": {
            "chat_context": {"latest_customer_message": "这款还有吗？"},
            "input_context": {"editable": True, "send_button_visible": True},
        },
        "focus_result": {"focused": True},
    }

    result = build_monitor_once_result(
        probe_result,
        previous_message="这款还有吗？",
        shop_id="shop_001",
        session_id="desktop-session-1",
    )

    assert result["ok"] is True
    assert result["status"] == "idle"
    assert result["reply"] is None
    assert result["fill_action"] is None


def test_build_monitor_once_result_composes_reply_for_new_message():
    probe_result = {
        "ok": True,
        "desktop_context": {
            "platform": "jd_customer_service",
            "confidence": 0.9,
            "active_customer": {"id": "jd_4a3d4c80e30ef", "name": "jd_4a3d4c80e30ef"},
            "chat_context": {
                "latest_customer_message": "这款还有吗？",
                "recent_messages": [],
                "contains_image": False,
            },
            "product_context": {"tab_active": False, "items": []},
            "user_order_context": {"user_labels": [], "orders": [], "service_forms": []},
            "input_context": {
                "editable": True,
                "has_smart_reply": False,
                "send_button_visible": True,
                "existing_text": "",
            },
        },
        "focus_result": {
            "focused": True,
            "target_bounds": [360, 690, 970, 1010],
            "target_automation_id": "reply-editor",
        },
    }

    result = build_monitor_once_result(
        probe_result,
        previous_message="",
        shop_id="shop_001",
        session_id="desktop-session-1",
    )

    assert result["ok"] is True
    assert result["status"] == "new_message"
    assert result["reply"]["reply_draft"]
    assert result["fill_action"]["target_bounds"] == [360, 690, 970, 1010]
    assert result["fill_action"]["target_automation_id"] == "reply-editor"
    assert result["fill_action"]["auto_send_allowed"] is False
