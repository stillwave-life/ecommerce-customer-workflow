from app.desktop.windows_adapter.jd_workspace_profile import get_jd_workspace_profile


EXPECTED_ACTIONS = {
    "view_product",
    "view_order",
    "view_service_form",
    "switch_right_tab_product",
    "switch_right_tab_order",
    "switch_right_tab_service",
}


def test_get_jd_workspace_profile_contains_regions_and_actions():
    profile = get_jd_workspace_profile()

    assert profile["name"] == "jd_maximized_default"
    assert profile["conversation_list_region"]
    assert profile["chat_region"]
    assert profile["right_panel_region"]
    assert profile["input_region"]
    assert profile["send_button_region"]
    assert profile["right_panel_click_targets"]
    assert EXPECTED_ACTIONS.issubset(profile["right_panel_click_targets"].keys())

    for bounds in [
        profile["conversation_list_region"],
        profile["chat_region"],
        profile["right_panel_region"],
        profile["input_region"],
        profile["send_button_region"],
        *profile["right_panel_click_targets"].values(),
    ]:
        assert len(bounds) == 4
        assert all(0 <= float(value) <= 1 for value in bounds)
