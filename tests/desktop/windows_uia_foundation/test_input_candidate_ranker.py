from app.desktop.windows_uia_foundation.input_candidate_ranker import rank_input_candidates


def test_rank_input_candidates_prefers_editable_bottom_text_area():
    nodes = [
        {
            "role": "edit",
            "name": "搜索框",
            "bounds": [1200, 150, 1600, 200],
            "editable": True,
            "clickable": True,
            "visible": True,
        },
        {
            "role": "edit",
            "name": "输入框",
            "bounds": [360, 690, 970, 1010],
            "editable": True,
            "clickable": True,
            "visible": True,
        },
    ]

    result = rank_input_candidates(nodes)

    assert result["ok"] is True
    assert result["candidates"][0]["node"]["name"] == "输入框"
    assert result["candidates"][0]["score"] > result["candidates"][1]["score"]
    assert "editable" in result["candidates"][0]["reasons"]


def test_rank_input_candidates_penalizes_invisible_and_disabled_nodes():
    nodes = [
        {
            "role": "edit",
            "name": "输入框",
            "bounds": [360, 690, 970, 1010],
            "editable": True,
            "clickable": True,
            "visible": False,
            "enabled": False,
        },
        {
            "role": "edit",
            "name": "主输入框",
            "bounds": [360, 690, 970, 1010],
            "editable": True,
            "clickable": True,
            "visible": True,
            "enabled": True,
        },
    ]

    result = rank_input_candidates(nodes)

    assert result["candidates"][0]["node"]["name"] == "主输入框"
    assert "visible" in result["candidates"][0]["reasons"]
    assert "disabled_penalty" in result["candidates"][1]["reasons"]
    assert "hidden_penalty" in result["candidates"][1]["reasons"]


def test_rank_input_candidates_accepts_generic_writable_box_for_wechat_style_ui():
    nodes = [
        {
            "role": "document",
            "name": "聊天输入区",
            "bounds": [260, 720, 980, 980],
            "editable": True,
            "clickable": False,
            "visible": True,
            "enabled": True,
        },
        {
            "role": "button",
            "name": "发送",
            "bounds": [1000, 920, 1080, 980],
            "editable": False,
            "clickable": True,
            "visible": True,
            "enabled": True,
        },
    ]

    result = rank_input_candidates(nodes)

    assert result["candidates"][0]["node"]["name"] == "聊天输入区"
    assert result["candidates"][0]["score"] > result["candidates"][1]["score"]
