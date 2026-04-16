from app.desktop.windows_adapter.ui_node_adapter import build_windows_node


def test_build_windows_node_normalizes_automation_fields():
    node = build_windows_node(
        role="edit",
        name="输入框",
        text="",
        bounds=[360, 690, 970, 1010],
        editable=True,
        clickable=True,
        visible=True,
        automation_id="reply-editor",
        control_type="Edit",
    )

    assert node["role"] == "edit"
    assert node["name"] == "输入框"
    assert node["bounds"] == [360, 690, 970, 1010]
    assert node["editable"] is True
    assert node["clickable"] is True
    assert node["visible"] is True
    assert node["automation_id"] == "reply-editor"
    assert node["control_type"] == "Edit"
