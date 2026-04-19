from app.desktop.windows_adapter.fill_executor import build_fill_execution_result


def test_build_fill_execution_result_reports_success():
    result = build_fill_execution_result(
        executed=True,
        verified=True,
        target_name="输入框",
        written_text="你好",
        verify_mode="readback_required",
        reason="",
    )

    assert result["ok"] is True
    assert result["executed"] is True
    assert result["verified"] is True
    assert result["target_name"] == "输入框"
    assert result["written_text"] == "你好"
    assert result["verify_mode"] == "readback_required"


def test_build_fill_execution_result_reports_failure():
    result = build_fill_execution_result(
        executed=False,
        verified=False,
        target_name="",
        written_text="",
        verify_mode="readback_required",
        reason="fill_execution_failed",
    )

    assert result["ok"] is False
    assert result["executed"] is False
    assert result["reason"] == "fill_execution_failed"
