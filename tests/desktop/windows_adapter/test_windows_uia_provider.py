from app.desktop.windows_adapter.windows_uia_provider import (
    collect_windows_uia_snapshot,
    provider_available,
)


def test_provider_available_is_false_without_backend_dependency():
    available = provider_available(importer=lambda: (_ for _ in ()).throw(ImportError("missing backend")))

    assert available is False


def test_collect_windows_uia_snapshot_returns_import_error_contract():
    result = collect_windows_uia_snapshot(importer=lambda: (_ for _ in ()).throw(ImportError("missing backend")))

    assert result["ok"] is False
    assert result["error"] == "windows_uia_import_failed"
    assert result["backend"]["type"] == "windows_uia"
    assert result["backend"]["live"] is True


def test_collect_windows_uia_snapshot_returns_collect_error_contract():
    class FakeBackend:
        @staticmethod
        def collect_snapshot():
            raise RuntimeError("uia collect failed")

    result = collect_windows_uia_snapshot(importer=lambda: FakeBackend)

    assert result["ok"] is False
    assert result["error"] == "windows_uia_collect_failed"
    assert result["backend"]["type"] == "windows_uia"


def test_collect_windows_uia_snapshot_uses_backend_module_contract():
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
                        "text": "",
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

    assert result["ok"] is True
    assert result["window"]["handle"] == 1001
    assert result["nodes"][0]["name"] == "输入框"


def test_collect_windows_uia_snapshot_keeps_normalized_first_level_nodes():
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
                        "role": "button",
                        "name": "发送(F1)",
                        "text": "发送(F1)",
                        "bounds": [1200, 920, 1320, 980],
                        "editable": False,
                        "clickable": True,
                        "visible": True,
                        "automation_id": "send-btn",
                        "control_type": "Button",
                        "class_name": "Button",
                        "value": "",
                        "enabled": True,
                        "parent_role": "pane",
                        "path": ["window", "footer", "send_button"],
                    }
                ],
            }

    result = collect_windows_uia_snapshot(importer=lambda: FakeBackend)

    assert result["nodes"][0]["class_name"] == "Button"
    assert result["nodes"][0]["parent_role"] == "pane"
    assert result["nodes"][0]["path"] == ["window", "footer", "send_button"]


def test_collect_windows_uia_snapshot_keeps_recursive_child_nodes():
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
                        "name": "聊天区",
                        "text": "",
                        "bounds": [300, 200, 1000, 780],
                        "editable": False,
                        "clickable": False,
                        "visible": True,
                        "automation_id": "chat-panel",
                        "control_type": "Pane",
                        "class_name": "Pane",
                        "value": "",
                        "enabled": True,
                        "parent_role": "window",
                        "path": ["window", "pane"],
                        "children": [
                            {
                                "role": "text",
                                "name": "客户消息",
                                "text": "这款还有吗？",
                                "bounds": [380, 320, 900, 420],
                                "editable": False,
                                "clickable": False,
                                "visible": True,
                                "automation_id": "",
                                "control_type": "Text",
                                "class_name": "TextBlock",
                                "value": "",
                                "enabled": True,
                                "parent_role": "pane",
                                "path": ["window", "pane", "text"],
                                "children": [],
                            }
                        ],
                    }
                ],
            }

    result = collect_windows_uia_snapshot(importer=lambda: FakeBackend)

    assert result["nodes"][0]["children"][0]["name"] == "客户消息"
    assert result["nodes"][0]["children"][0]["path"] == ["window", "pane", "text"]


def test_collect_windows_uia_snapshot_limits_recursive_depth():
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
                        "name": "根节点",
                        "text": "",
                        "bounds": [0, 0, 100, 100],
                        "editable": False,
                        "clickable": False,
                        "visible": True,
                        "automation_id": "root",
                        "control_type": "Pane",
                        "class_name": "Pane",
                        "value": "",
                        "enabled": True,
                        "parent_role": "window",
                        "path": ["window", "pane"],
                        "children": [
                            {
                                "role": "pane",
                                "name": "第二层",
                                "text": "",
                                "bounds": [0, 0, 100, 100],
                                "editable": False,
                                "clickable": False,
                                "visible": True,
                                "automation_id": "child",
                                "control_type": "Pane",
                                "class_name": "Pane",
                                "value": "",
                                "enabled": True,
                                "parent_role": "pane",
                                "path": ["window", "pane", "pane"],
                                "children": [
                                    {
                                        "role": "text",
                                        "name": "第三层消息",
                                        "text": "需要被截断",
                                        "bounds": [0, 0, 100, 100],
                                        "editable": False,
                                        "clickable": False,
                                        "visible": True,
                                        "automation_id": "deep",
                                        "control_type": "Text",
                                        "class_name": "TextBlock",
                                        "value": "",
                                        "enabled": True,
                                        "parent_role": "pane",
                                        "path": ["window", "pane", "pane", "text"],
                                        "children": [],
                                    }
                                ],
                            }
                        ],
                    }
                ],
            }

    result = collect_windows_uia_snapshot(importer=lambda: FakeBackend)

    assert result["nodes"][0]["children"][0]["name"] == "第二层"
    assert result["nodes"][0]["children"][0]["children"][0]["name"] == "第三层消息"
