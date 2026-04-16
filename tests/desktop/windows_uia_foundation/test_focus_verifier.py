from app.desktop.windows_uia_foundation.focus_verifier import build_focus_verification


def test_build_focus_verification_reports_success():
    result = build_focus_verification(focused=True, target_name="输入框")

    assert result["ok"] is True
    assert result["focused"] is True
    assert result["target_name"] == "输入框"
    assert result["reason"] == ""


def test_build_focus_verification_reports_failure():
    result = build_focus_verification(focused=False, target_name="", reason="focus_verification_failed")

    assert result["ok"] is False
    assert result["focused"] is False
    assert result["reason"] == "focus_verification_failed"
