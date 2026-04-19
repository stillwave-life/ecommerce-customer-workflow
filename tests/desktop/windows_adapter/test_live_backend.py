from app.desktop.windows_adapter.live_backend import collect_live_uia_snapshot


def test_collect_live_uia_snapshot_reports_import_failure_without_provider():
    result = collect_live_uia_snapshot()

    assert result["ok"] is False
    assert result["error"] == "windows_uia_import_failed"
    assert result["backend"]["type"] == "windows_uia"
    assert result["backend"]["live"] is True


def test_collect_live_uia_snapshot_uses_provider_contract():
    def provider():
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

    result = collect_live_uia_snapshot(provider=provider)

    assert result["ok"] is True
    assert result["backend"] == {"type": "windows_uia", "live": True}
    assert result["window"]["handle"] == 1001
    assert result["nodes"][0]["name"] == "输入框"
