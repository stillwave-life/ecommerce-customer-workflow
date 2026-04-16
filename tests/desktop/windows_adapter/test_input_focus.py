from app.desktop.windows_adapter.input_focus import build_focus_result


def test_build_focus_result_reports_successful_focus():
    result = build_focus_result(
        focused=True,
        target_role="edit",
        target_name="输入框",
        reason="",
    )

    assert result["ok"] is True
    assert result["focused"] is True
    assert result["target_role"] == "edit"
    assert result["target_name"] == "输入框"
    assert result["reason"] == ""


def test_build_focus_result_reports_failure_reason():
    result = build_focus_result(
        focused=False,
        target_role="",
        target_name="",
        reason="input_box_not_found",
    )

    assert result["ok"] is False
    assert result["focused"] is False
    assert result["reason"] == "input_box_not_found"
