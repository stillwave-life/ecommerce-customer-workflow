from app.desktop.windows_adapter.region_input_bridge import build_region_input_nodes


def test_build_region_input_nodes_adds_region_hints_for_perception_pipeline():
    nodes = [
        {"role": "listitem", "text": "这款还有吗？", "control_type": "Text", "region_hint": "chat"},
        {"role": "edit", "text": "", "control_type": "Edit", "region_hint": "input"},
    ]

    result = build_region_input_nodes(nodes)

    assert result[0]["region_hint"] == "chat"
    assert result[1]["region_hint"] == "input"
