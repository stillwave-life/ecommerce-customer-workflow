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
