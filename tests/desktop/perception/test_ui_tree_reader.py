from app.desktop.perception.ui_tree_reader import build_ui_tree_result


def test_build_ui_tree_result_preserves_nodes_and_bounds():
    nodes = [
        {
            "role": "edit",
            "name": "输入框",
            "text": "",
            "bounds": [360, 690, 970, 1010],
            "editable": True,
            "clickable": True,
            "children": [],
        }
    ]

    result = build_ui_tree_result(nodes=nodes)

    assert result["ok"] is True
    assert result["nodes"][0]["role"] == "edit"
    assert result["nodes"][0]["editable"] is True
    assert result["nodes"][0]["bounds"] == [360, 690, 970, 1010]
