from app.desktop.windows_uia_foundation.diagnostics_report import build_diagnostics_report


def test_build_diagnostics_report_aggregates_probe_candidates_gate_and_focus():
    report = build_diagnostics_report(
        window={"title": "evw10158991"},
        node_stats={"node_count": 423},
        input_candidates=[{"score": 0.86}],
        gate_result={"decision": "allow_focus"},
        focus_result={"focused": True},
        desktop_context={"platform": "jd_customer_service"},
    )

    assert report["window"]["title"] == "evw10158991"
    assert report["node_stats"]["node_count"] == 423
    assert report["input_candidates"][0]["score"] == 0.86
    assert report["gate_result"]["decision"] == "allow_focus"
    assert report["focus_result"]["focused"] is True
    assert report["desktop_context"]["platform"] == "jd_customer_service"


def test_build_diagnostics_report_keeps_backend_metadata():
    report = build_diagnostics_report(
        window={"title": "evw10158991"},
        node_stats={"node_count": 423},
        input_candidates=[{"score": 0.86}],
        gate_result={"decision": "allow_focus"},
        focus_result={"focused": True},
        desktop_context={"platform": "jd_customer_service"},
        backend={"type": "windows_uia", "live": False},
    )

    assert report["backend"]["type"] == "windows_uia"
    assert report["backend"]["live"] is False
