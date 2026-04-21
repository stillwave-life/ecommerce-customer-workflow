from __future__ import annotations

from app.desktop.windows_adapter.jd_workspace_profile import get_jd_workspace_profile


def build_right_panel_actions(profile_name: str = "jd_maximized_default", desktop_context: dict | None = None) -> list[dict]:
    profile = get_jd_workspace_profile(profile_name)
    targets = profile.get("right_panel_click_targets", {})
    actions = []
    for name, bounds in targets.items():
        actions.append(
            {
                "name": name,
                "targeting_strategy": "coordinates",
                "target_bounds": bounds,
                "panel": "right_panel",
                "enabled": True,
            }
        )
    return actions
