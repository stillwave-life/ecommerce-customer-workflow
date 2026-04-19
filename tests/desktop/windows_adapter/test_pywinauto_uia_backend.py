from app.desktop.windows_adapter.ui_node_adapter import build_windows_node
from app.desktop.windows_adapter.windows_uia_provider import collect_windows_uia_snapshot


def test_build_windows_node_keeps_value_separate_from_text():
    node = build_windows_node(
        role="edit",
        name="输入框",
        text="显示文本",
        value="真实输入值",
        bounds=[360, 690, 970, 1010],
        editable=True,
        clickable=True,
        visible=True,
        control_type="Edit",
    )

    assert node["text"] == "显示文本"
    assert node["value"] == "真实输入值"


def test_collect_windows_uia_snapshot_prefers_value_for_edit_nodes():
    class FakeBackend:
        @staticmethod
        def collect_snapshot():
            return {
                "window": {
                    "handle": 1001,
                    "title": "evw10158991",
                    "process_name": "jd-workbench.exe",
                    "bounds": [0, 0, 1680, 1048],
                    "is_foreground": True,
                },
                "nodes": [
                    {
                        "role": "edit",
                        "name": "输入框",
                        "text": "显示文本",
                        "value": "真实输入值",
                        "bounds": [360, 690, 970, 1010],
                        "editable": True,
                        "clickable": True,
                        "visible": True,
                        "automation_id": "reply-editor",
                        "control_type": "Edit",
                        "enabled": True,
                        "path": ["window", "footer", "reply_editor"],
                    }
                ],
            }

    result = collect_windows_uia_snapshot(importer=lambda: FakeBackend)

    assert result["nodes"][0]["value"] == "真实输入值"


def test_collect_windows_uia_snapshot_filters_invisible_empty_noise_nodes():
    class FakeBackend:
        @staticmethod
        def collect_snapshot():
            return {
                "window": {
                    "handle": 1001,
                    "title": "evw10158991",
                    "process_name": "jd-workbench.exe",
                    "bounds": [0, 0, 1680, 1048],
                    "is_foreground": True,
                },
                "nodes": [
                    {
                        "role": "pane",
                        "name": "",
                        "text": "",
                        "value": "",
                        "bounds": [0, 0, 0, 0],
                        "editable": False,
                        "clickable": False,
                        "visible": False,
                        "automation_id": "",
                        "control_type": "Pane",
                        "enabled": False,
                        "path": ["window", "pane"],
                    },
                    {
                        "role": "button",
                        "name": "发送",
                        "text": "发送",
                        "value": "",
                        "bounds": [1200, 920, 1320, 980],
                        "editable": False,
                        "clickable": True,
                        "visible": True,
                        "automation_id": "send-btn",
                        "control_type": "Button",
                        "enabled": True,
                        "path": ["window", "button"],
                    },
                ],
            }

    result = collect_windows_uia_snapshot(importer=lambda: FakeBackend)

    assert len(result["nodes"]) == 1
    assert result["nodes"][0]["name"] == "发送"
