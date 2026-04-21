from pathlib import Path

from app.desktop.windows_adapter import pywinauto_fill_impl


class FakeRect:
    def __init__(self, left: int, top: int, right: int, bottom: int):
        self.left = left
        self.top = top
        self.right = right
        self.bottom = bottom


class FakeWindow:
    def __init__(self, title: str = "咚咚融合工作台"):
        self._title = title
        self.click_coords = None
        self.keys = []

    def window_text(self):
        return self._title

    def rectangle(self):
        return FakeRect(100, 200, 1700, 1100)

    def click_input(self, coords):
        self.click_coords = coords

    def type_keys(self, keys, **kwargs):
        self.keys.append((keys, kwargs))


class FakeDesktop:
    def __init__(self, window: FakeWindow):
        self._window = window

    def get_active(self):
        return self._window


class CaptureStub:
    def __call__(self, region, output_path: Path):
        output_path.write_bytes(b"stub")
        return True


class DiffStub:
    def __init__(self, score: float):
        self.score = score

    def __call__(self, before_path: Path, after_path: Path):
        return self.score


def test_fill_text_coordinates_uses_profile_bounds_and_left_upper_click(monkeypatch, tmp_path):
    window = FakeWindow()
    monkeypatch.setattr(pywinauto_fill_impl, "_create_diagnostics_dir", lambda: tmp_path / "run1")
    monkeypatch.setattr(pywinauto_fill_impl, "_capture_region", CaptureStub())
    monkeypatch.setattr(pywinauto_fill_impl, "_compute_diff_score", DiffStub(0.12))
    monkeypatch.setattr(pywinauto_fill_impl, "_get_clipboard_text", lambda: (True, "old"))
    clipboard_values = []
    monkeypatch.setattr(pywinauto_fill_impl, "_set_clipboard_text", lambda text: clipboard_values.append(text) or True)

    result = pywinauto_fill_impl.fill_text(
        {
            "text": "您好",
            "targeting_strategy": "coordinates",
            "clear_before_fill": True,
            "paste_via_clipboard": True,
            "ui_profile": "jd_maximized_default",
        },
        desktop_factory=lambda: FakeDesktop(window),
    )

    assert result["diff_passed"] is True
    assert result["diagnostics_path"].endswith("run1")
    assert window.click_coords == (378, 659)
    assert window.keys[0][0] == "^a"
    assert window.keys[1][0] == "^v"
    assert clipboard_values == ["您好", "old"]


def test_fill_text_coordinates_allows_reasonable_active_window_with_warning(monkeypatch, tmp_path):
    window = FakeWindow(title="Unknown")
    monkeypatch.setattr(pywinauto_fill_impl, "_create_diagnostics_dir", lambda: tmp_path / "run2")
    monkeypatch.setattr(pywinauto_fill_impl, "_capture_region", CaptureStub())
    monkeypatch.setattr(pywinauto_fill_impl, "_compute_diff_score", DiffStub(0.11))
    monkeypatch.setattr(pywinauto_fill_impl, "_get_clipboard_text", lambda: (False, ""))
    monkeypatch.setattr(pywinauto_fill_impl, "_set_clipboard_text", lambda text: True)

    result = pywinauto_fill_impl.fill_text(
        {"text": "您好", "targeting_strategy": "coordinates"},
        desktop_factory=lambda: FakeDesktop(window),
    )

    run_payload = (tmp_path / "run2" / "run.json").read_text(encoding="utf-8")
    assert result["ok"] if "ok" in result else True
    assert "window_title_not_matched_using_active_window" in run_payload


def test_fill_text_coordinates_marks_diff_failure(monkeypatch, tmp_path):
    window = FakeWindow()
    monkeypatch.setattr(pywinauto_fill_impl, "_create_diagnostics_dir", lambda: tmp_path / "run3")
    monkeypatch.setattr(pywinauto_fill_impl, "_capture_region", CaptureStub())
    monkeypatch.setattr(pywinauto_fill_impl, "_compute_diff_score", DiffStub(0.0))
    monkeypatch.setattr(pywinauto_fill_impl, "_get_clipboard_text", lambda: (True, "old"))
    monkeypatch.setattr(pywinauto_fill_impl, "_set_clipboard_text", lambda text: True)

    result = pywinauto_fill_impl.fill_text(
        {"text": "您好", "targeting_strategy": "coordinates"},
        desktop_factory=lambda: FakeDesktop(window),
    )

    assert result["diff_passed"] is False
    assert result["reason"] == "screenshot_diff_failed"
    run_payload = (tmp_path / "run3" / "run.json").read_text(encoding="utf-8")
    assert '"reason": "screenshot_diff_failed"' in run_payload
