from app.desktop.perception.window_probe import build_window_probe_result


def test_build_window_probe_result_marks_jd_candidate_window():
    result = build_window_probe_result(
        window_title="evw10158991",
        process_name="jd-workbench.exe",
        window_bounds=[0, 0, 1680, 1048],
        is_foreground=True,
        platform_hint="jd_customer_service",
        confidence=0.82,
    )

    assert result["ok"] is True
    assert result["window_title"] == "evw10158991"
    assert result["platform_hint"] == "jd_customer_service"
    assert result["confidence"] == 0.82
