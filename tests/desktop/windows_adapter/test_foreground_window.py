from app.desktop.windows_adapter.foreground_window import build_foreground_window_result


def test_build_foreground_window_result_preserves_window_metadata():
    result = build_foreground_window_result(
        handle=1001,
        title="evw10158991",
        process_name="jd-workbench.exe",
        bounds=[0, 0, 1680, 1048],
        is_foreground=True,
    )

    assert result["ok"] is True
    assert result["handle"] == 1001
    assert result["title"] == "evw10158991"
    assert result["process_name"] == "jd-workbench.exe"
    assert result["bounds"] == [0, 0, 1680, 1048]
    assert result["is_foreground"] is True
