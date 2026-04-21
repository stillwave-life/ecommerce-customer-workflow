from app.desktop.windows_adapter.fill_provider import execute_fill_with_provider


def test_execute_fill_with_provider_rejects_empty_text():
    result = execute_fill_with_provider(
        {"text": "", "verify_mode": "readback_required"},
        provider=lambda action: {"target_name": "输入框", "written_text": ""},
    )

    assert result["ok"] is False
    assert result["reason"] == "reply text is required"


def test_execute_fill_with_provider_reports_success_when_readback_matches():
    def provider(action):
        return {"target_name": "输入框", "written_text": action["text"]}

    result = execute_fill_with_provider(
        {"text": "你好", "verify_mode": "readback_required"},
        provider=provider,
    )

    assert result["ok"] is True
    assert result["executed"] is True
    assert result["verified"] is True
    assert result["written_text"] == "你好"


def test_execute_fill_with_provider_reports_readback_mismatch():
    def provider(action):
        return {"target_name": "输入框", "written_text": "错误文本"}

    result = execute_fill_with_provider(
        {"text": "你好", "verify_mode": "readback_required"},
        provider=provider,
    )

    assert result["ok"] is False
    assert result["executed"] is True
    assert result["verified"] is False
    assert result["reason"] == "readback_mismatch"


def test_execute_fill_with_provider_uses_screenshot_diff_verification_success():
    def provider(action):
        return {
            "target_name": "输入框",
            "written_text": action["text"],
            "verification_method": "screenshot_diff",
            "diff_score": 0.12,
            "diff_passed": True,
            "diagnostics_path": "C:/tmp/after.png",
        }

    result = execute_fill_with_provider(
        {"text": "你好", "verify_mode": "screenshot_diff_required"},
        provider=provider,
    )

    assert result["ok"] is True
    assert result["verified"] is True
    assert result["verification_method"] == "screenshot_diff"
    assert result["diff_passed"] is True


def test_execute_fill_with_provider_uses_screenshot_diff_verification_failure():
    def provider(action):
        return {
            "target_name": "输入框",
            "written_text": action["text"],
            "verification_method": "screenshot_diff",
            "diff_score": 0.0,
            "diff_passed": False,
        }

    result = execute_fill_with_provider(
        {"text": "你好", "verify_mode": "screenshot_diff_required"},
        provider=provider,
    )

    assert result["ok"] is False
    assert result["verified"] is False
    assert result["reason"] == "screenshot_diff_failed"
