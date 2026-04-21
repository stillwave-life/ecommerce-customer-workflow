from __future__ import annotations

JD_MAXIMIZED_PROFILE = {
    "name": "jd_maximized_default",
    "conversation_list_region": [0.00, 0.10, 0.16, 0.93],
    "chat_region": [0.16, 0.10, 0.68, 0.80],
    "right_panel_region": [0.70, 0.10, 0.99, 0.92],
    "input_region": [0.18, 0.82, 0.80, 0.96],
    "send_button_region": [0.56, 0.93, 0.63, 0.98],
    "right_panel_click_targets": {
        "view_product": [0.77, 0.18, 0.96, 0.34],
        "view_order": [0.75, 0.73, 0.87, 0.77],
        "view_service_form": [0.88, 0.73, 0.98, 0.77],
        "switch_right_tab_product": [0.72, 0.11, 0.80, 0.16],
        "switch_right_tab_order": [0.80, 0.11, 0.88, 0.16],
        "switch_right_tab_service": [0.88, 0.11, 0.97, 0.16],
    },
}


def get_jd_workspace_profile(profile_name: str = "jd_maximized_default") -> dict:
    if profile_name != JD_MAXIMIZED_PROFILE["name"]:
        return JD_MAXIMIZED_PROFILE.copy()
    return JD_MAXIMIZED_PROFILE.copy()
