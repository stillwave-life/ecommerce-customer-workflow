from app.desktop.fill_action import build_fill_action
from app.desktop.windows_adapter.fill_executor import build_fill_execution_result


def test_fill_action_and_executor_contracts_align():
    action = build_fill_action(
        "你好",
        target="reply_box",
        target_bounds=[360, 690, 970, 1010],
        target_automation_id="reply-editor",
        verify_mode="readback_required",
    )
    result = build_fill_execution_result(
        executed=True,
        verified=True,
        target_name="输入框",
        written_text=action["text"],
        verify_mode=action["verify_mode"],
        reason="",
    )

    assert action["ok"] is True
    assert result["ok"] is True
    assert result["written_text"] == action["text"]
    assert result["verify_mode"] == action["verify_mode"]
