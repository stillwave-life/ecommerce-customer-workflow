from app.desktop.windows_adapter.pywinauto_fill_backend import provider_available
from app.desktop.windows_adapter.pywinauto_fill_impl import fill_text


def test_pywinauto_fill_backend_reports_unavailable_without_dependency():
    available = provider_available(importer=lambda: (_ for _ in ()).throw(ImportError("missing backend")))

    assert available is False


def test_fill_text_prefers_automation_id_locator():
    class FakeControl:
        def __init__(self) -> None:
            self.value = ""

        def set_edit_text(self, text: str) -> None:
            self.value = text

        def window_text(self) -> str:
            return self.value

    class FakeDesktop:
        def __init__(self) -> None:
            self.control = FakeControl()
            self.last_kwargs = None

        def window(self, **kwargs):
            self.last_kwargs = kwargs
            return self.control

    desktop = FakeDesktop()
    result = fill_text(
        {
            "text": "你好",
            "target_automation_id": "reply-editor",
            "target_name": "输入框",
        },
        desktop_factory=lambda: desktop,
    )

    assert desktop.last_kwargs == {"auto_id": "reply-editor"}
    assert result["written_text"] == "你好"
    assert result["target_name"] == "输入框"


def test_fill_text_falls_back_to_title_locator():
    class FakeControl:
        def __init__(self) -> None:
            self.value = ""

        def set_edit_text(self, text: str) -> None:
            self.value = text

        def window_text(self) -> str:
            return self.value

    class FakeDesktop:
        def __init__(self) -> None:
            self.control = FakeControl()
            self.calls = []

        def window(self, **kwargs):
            self.calls.append(kwargs)
            return self.control

    desktop = FakeDesktop()
    result = fill_text(
        {
            "text": "你好",
            "target_name": "微信输入框",
        },
        desktop_factory=lambda: desktop,
    )

    assert desktop.calls[-1] == {"title": "微信输入框"}
    assert result["written_text"] == "你好"
