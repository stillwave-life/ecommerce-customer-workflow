from app.desktop.windows_adapter.region_input_bridge import build_region_input_nodes
from app.desktop.windows_adapter.ui_node_adapter import build_windows_node


def test_build_region_input_nodes_adds_region_hints_for_perception_pipeline():
    nodes = [
        {"role": "listitem", "text": "这款还有吗？", "control_type": "Text", "region_hint": "chat"},
        {"role": "edit", "text": "", "control_type": "Edit", "region_hint": "input"},
    ]

    result = build_region_input_nodes(nodes)

    assert result[0]["region_hint"] == "chat"
    assert result[1]["region_hint"] == "input"


def test_build_region_input_nodes_infers_regions_from_uia_style_nodes():
    nodes = [
        build_windows_node(
            role="text",
            name="客户消息",
            text="这款还有吗？",
            bounds=[380, 320, 900, 420],
            editable=False,
            clickable=False,
            visible=True,
            control_type="Text",
            class_name="TextBlock",
            parent_role="list",
            path=["window", "chat_panel", "message_list"],
        ),
        build_windows_node(
            role="edit",
            name="输入框",
            text="",
            bounds=[360, 690, 970, 1010],
            editable=True,
            clickable=True,
            visible=True,
            automation_id="reply-editor",
            control_type="Edit",
            class_name="RichEdit",
            enabled=True,
            parent_role="pane",
            path=["window", "footer", "reply_editor"],
        ),
        build_windows_node(
            role="button",
            name="发送(F1)",
            text="发送(F1)",
            bounds=[1200, 920, 1320, 980],
            editable=False,
            clickable=True,
            visible=True,
            automation_id="send-btn",
            control_type="Button",
            class_name="Button",
            enabled=True,
            parent_role="pane",
            path=["window", "footer", "send_button"],
        ),
    ]

    result = build_region_input_nodes(nodes)

    assert result[0]["region_hint"] == "chat"
    assert result[0]["message_role"] == "customer"
    assert result[1]["region_hint"] == "input"
    assert result[1]["existing_text"] == ""
    assert result[2]["region_hint"] == "send_button"
    assert result[2]["visible"] is True


def test_build_region_input_nodes_infers_from_provider_first_level_nodes():
    nodes = [
        {
            "role": "edit",
            "name": "回复编辑器",
            "text": "",
            "bounds": [360, 690, 970, 1010],
            "editable": True,
            "clickable": False,
            "visible": True,
            "automation_id": "",
            "control_type": "Edit",
            "class_name": "RichEdit",
            "value": "真实输入值",
            "enabled": True,
            "parent_role": "window",
            "path": ["window", "edit"],
            "children": [],
        },
        {
            "role": "button",
            "name": "发送",
            "text": "发送",
            "bounds": [1200, 920, 1320, 980],
            "editable": False,
            "clickable": True,
            "visible": True,
            "automation_id": "",
            "control_type": "Button",
            "class_name": "Button",
            "value": "",
            "enabled": True,
            "parent_role": "window",
            "path": ["window", "button"],
            "children": [],
        },
    ]

    result = build_region_input_nodes(nodes)

    assert result[0]["region_hint"] == "input"
    assert result[0]["existing_text"] == "真实输入值"
    assert result[1]["region_hint"] == "send_button"


def test_build_region_input_nodes_flattens_recursive_provider_children():
    nodes = [
        {
            "role": "pane",
            "name": "聊天区",
            "text": "",
            "bounds": [300, 200, 1000, 780],
            "editable": False,
            "clickable": False,
            "visible": True,
            "control_type": "Pane",
            "path": ["window", "pane"],
            "children": [
                {
                    "role": "text",
                    "name": "客户消息",
                    "text": "这款还有吗？",
                    "bounds": [380, 320, 900, 420],
                    "editable": False,
                    "clickable": False,
                    "visible": True,
                    "control_type": "Text",
                    "path": ["window", "pane", "text"],
                    "children": [],
                }
            ],
        }
    ]

    result = build_region_input_nodes(nodes)

    assert len(result) == 2
    assert result[1]["region_hint"] == "chat"
    assert result[1]["message_role"] == "customer"


def test_build_region_input_nodes_marks_generic_writable_box_as_input():
    nodes = [
        {
            "role": "document",
            "name": "聊天输入区",
            "text": "",
            "value": "微信草稿",
            "bounds": [260, 720, 980, 980],
            "editable": True,
            "clickable": False,
            "visible": True,
            "enabled": True,
            "control_type": "Document",
            "path": ["window", "document"],
            "children": [],
        }
    ]

    result = build_region_input_nodes(nodes)

    assert result[0]["region_hint"] == "input"
    assert result[0]["existing_text"] == "微信草稿"
