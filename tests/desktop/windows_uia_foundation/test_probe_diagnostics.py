from app.desktop.windows_uia_foundation.probe_diagnostics import build_probe_diagnostics


def test_build_probe_diagnostics_summarizes_node_counts():
    diagnostics = build_probe_diagnostics(
        window={"title": "evw10158991", "handle": 1001},
        node_count=423,
        editable_node_count=3,
        clickable_node_count=27,
        visible_node_count=390,
    )

    assert diagnostics["ok"] is True
    assert diagnostics["window"]["title"] == "evw10158991"
    assert diagnostics["node_stats"]["node_count"] == 423
    assert diagnostics["node_stats"]["editable_node_count"] == 3
    assert diagnostics["node_stats"]["clickable_node_count"] == 27
    assert diagnostics["node_stats"]["visible_node_count"] == 390
