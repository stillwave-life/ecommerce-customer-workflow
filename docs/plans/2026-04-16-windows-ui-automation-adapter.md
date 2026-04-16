# Windows UI Automation Adapter Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build the first Windows UI Automation adapter layer that reads the real foreground JD workspace window, converts automation nodes into the existing perception pipeline format, and adds safe input-focus capability without writing or sending messages.

**Architecture:** Add a new `app/desktop/windows_adapter/` package that isolates real Windows foreground-window probing, UI Automation node normalization, region-input bridging, and input-focus actions from the existing `app/desktop/perception/` parsing pipeline. The adapter layer produces structured inputs for `region_classifier` and `jd_workspace_parser`, and returns a separate `focus_result` object so read-path and action-path remain decoupled.

**Tech Stack:** Python, pytest, existing `app/desktop` contracts, Windows-oriented adapter abstractions, JSON-style script entrypoints.

---

## Context and Constraints

Read these files before implementation:

- `docs/windows-ui-automation-adapter-direction.md`
- `docs/jd-customer-service-ui-perception-direction.md`
- `docs/plans/2026-04-16-jd-customer-service-ui-perception.md`
- `app/desktop/perception/window_probe.py`
- `app/desktop/perception/ui_tree_reader.py`
- `app/desktop/perception/region_classifier.py`
- `app/desktop/perception/jd_workspace_parser.py`
- `app/desktop/launcher.py`

Hard constraints:

- Do not implement text fill or send actions.
- Do not remove or bypass the existing `desktop_context -> launcher -> prepare_mapper -> reply_composer -> fill_action` flow.
- Keep real Windows adapter code in a separate package from perception parsing logic.
- Input focus must remain independent from fill actions.
- OCR is not the primary route in this phase.
- The first implementation must be testable without a real Windows automation backend by using structured adapter inputs.

Recommended verification command after each task:

```bash
py -3 -m pytest tests
```

If `py -3` is unavailable, use:

```bash
python3 -m pytest tests
```

---

### Task 1: Add Windows Foreground Window Probe Contract

**Files:**
- Create: `app/desktop/windows_adapter/__init__.py`
- Create: `app/desktop/windows_adapter/foreground_window.py`
- Test: `tests/desktop/windows_adapter/test_foreground_window.py`

**Step 1: Write the failing test**

Create `tests/desktop/windows_adapter/test_foreground_window.py`:

```python
from app.desktop.windows_adapter.foreground_window import build_foreground_window_result


def test_build_foreground_window_result_preserves_window_metadata():
    result = build_foreground_window_result(
        handle=1001,
        title="evw10158991",
        process_name="jd-workbench.exe",
        bounds=[0, 0, 1680, 1048],
        is_foreground=True,
    )

    assert result["ok"] is True
    assert result["handle"] == 1001
    assert result["title"] == "evw10158991"
    assert result["process_name"] == "jd-workbench.exe"
    assert result["bounds"] == [0, 0, 1680, 1048]
    assert result["is_foreground"] is True
```

**Step 2: Run test to verify it fails**

Run:

```bash
py -3 -m pytest tests/desktop/windows_adapter/test_foreground_window.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'app.desktop.windows_adapter.foreground_window'`.

**Step 3: Write minimal implementation**

Create `app/desktop/windows_adapter/__init__.py` as an empty package file.

Create `app/desktop/windows_adapter/foreground_window.py`:

```python
from __future__ import annotations


def build_foreground_window_result(
    *,
    handle: int,
    title: str,
    process_name: str,
    bounds: list[int],
    is_foreground: bool,
) -> dict:
    return {
        "ok": True,
        "handle": handle,
        "title": title,
        "process_name": process_name,
        "bounds": list(bounds),
        "is_foreground": is_foreground,
    }
```

**Step 4: Run test to verify it passes**

Run:

```bash
py -3 -m pytest tests/desktop/windows_adapter/test_foreground_window.py -v
```

Expected: PASS.

**Step 5: Run full tests**

Run:

```bash
py -3 -m pytest tests
```

Expected: PASS.

**Step 6: Commit**

```bash
git add app/desktop/windows_adapter/__init__.py app/desktop/windows_adapter/foreground_window.py tests/desktop/windows_adapter/test_foreground_window.py
git commit -m "feat: add windows foreground window contract"
```

---

### Task 2: Add Windows Automation Node Adapter

**Files:**
- Create: `app/desktop/windows_adapter/ui_node_adapter.py`
- Test: `tests/desktop/windows_adapter/test_ui_node_adapter.py`

**Step 1: Write the failing test**

Create `tests/desktop/windows_adapter/test_ui_node_adapter.py`:

```python
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
```

**Step 2: Run test to verify it fails**

Run:

```bash
py -3 -m pytest tests/desktop/windows_adapter/test_ui_node_adapter.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'app.desktop.windows_adapter.ui_node_adapter'`.

**Step 3: Write minimal implementation**

Create `app/desktop/windows_adapter/ui_node_adapter.py`:

```python
from __future__ import annotations


def build_windows_node(
    *,
    role: str,
    name: str,
    text: str,
    bounds: list[int],
    editable: bool,
    clickable: bool,
    visible: bool,
    automation_id: str = "",
    control_type: str = "",
) -> dict:
    return {
        "role": role,
        "name": name,
        "text": text,
        "bounds": list(bounds),
        "editable": editable,
        "clickable": clickable,
        "visible": visible,
        "automation_id": automation_id,
        "control_type": control_type,
        "children": [],
    }
```

**Step 4: Run test to verify it passes**

Run:

```bash
py -3 -m pytest tests/desktop/windows_adapter/test_ui_node_adapter.py -v
```

Expected: PASS.

**Step 5: Run full tests**

Run:

```bash
py -3 -m pytest tests
```

Expected: PASS.

**Step 6: Commit**

```bash
git add app/desktop/windows_adapter/ui_node_adapter.py tests/desktop/windows_adapter/test_ui_node_adapter.py
git commit -m "feat: add windows automation node adapter"
```

---

### Task 3: Add Region Input Bridge

**Files:**
- Create: `app/desktop/windows_adapter/region_input_bridge.py`
- Test: `tests/desktop/windows_adapter/test_region_input_bridge.py`

**Step 1: Write the failing test**

Create `tests/desktop/windows_adapter/test_region_input_bridge.py`:

```python
from app.desktop.windows_adapter.region_input_bridge import build_region_input_nodes


def test_build_region_input_nodes_adds_region_hints_for_perception_pipeline():
    nodes = [
        {"role": "listitem", "text": "这款还有吗？", "control_type": "Text", "region_hint": "chat"},
        {"role": "edit", "text": "", "control_type": "Edit", "region_hint": "input"},
    ]

    result = build_region_input_nodes(nodes)

    assert result[0]["region_hint"] == "chat"
    assert result[1]["region_hint"] == "input"
```

**Step 2: Run test to verify it fails**

Run:

```bash
py -3 -m pytest tests/desktop/windows_adapter/test_region_input_bridge.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'app.desktop.windows_adapter.region_input_bridge'`.

**Step 3: Write minimal implementation**

Create `app/desktop/windows_adapter/region_input_bridge.py`:

```python
from __future__ import annotations

from typing import Any


def build_region_input_nodes(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [node.copy() for node in nodes]
```

**Step 4: Run test to verify it passes**

Run:

```bash
py -3 -m pytest tests/desktop/windows_adapter/test_region_input_bridge.py -v
```

Expected: PASS.

**Step 5: Run full tests**

Run:

```bash
py -3 -m pytest tests
```

Expected: PASS.

**Step 6: Commit**

```bash
git add app/desktop/windows_adapter/region_input_bridge.py tests/desktop/windows_adapter/test_region_input_bridge.py
git commit -m "feat: add windows region input bridge"
```

---

### Task 4: Add Input Focus Result Contract

**Files:**
- Create: `app/desktop/windows_adapter/input_focus.py`
- Test: `tests/desktop/windows_adapter/test_input_focus.py`

**Step 1: Write the failing tests**

Create `tests/desktop/windows_adapter/test_input_focus.py`:

```python
from app.desktop.windows_adapter.input_focus import build_focus_result


def test_build_focus_result_reports_successful_focus():
    result = build_focus_result(
        focused=True,
        target_role="edit",
        target_name="输入框",
        reason="",
    )

    assert result["ok"] is True
    assert result["focused"] is True
    assert result["target_role"] == "edit"
    assert result["target_name"] == "输入框"
    assert result["reason"] == ""


def test_build_focus_result_reports_failure_reason():
    result = build_focus_result(
        focused=False,
        target_role="",
        target_name="",
        reason="input_box_not_found",
    )

    assert result["ok"] is False
    assert result["focused"] is False
    assert result["reason"] == "input_box_not_found"
```

**Step 2: Run test to verify it fails**

Run:

```bash
py -3 -m pytest tests/desktop/windows_adapter/test_input_focus.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'app.desktop.windows_adapter.input_focus'`.

**Step 3: Write minimal implementation**

Create `app/desktop/windows_adapter/input_focus.py`:

```python
from __future__ import annotations


def build_focus_result(
    *,
    focused: bool,
    target_role: str,
    target_name: str,
    reason: str,
) -> dict:
    return {
        "ok": focused,
        "focused": focused,
        "target_role": target_role,
        "target_name": target_name,
        "reason": reason,
    }
```

**Step 4: Run test to verify it passes**

Run:

```bash
py -3 -m pytest tests/desktop/windows_adapter/test_input_focus.py -v
```

Expected: PASS.

**Step 5: Run full tests**

Run:

```bash
py -3 -m pytest tests
```

Expected: PASS.

**Step 6: Commit**

```bash
git add app/desktop/windows_adapter/input_focus.py tests/desktop/windows_adapter/test_input_focus.py
git commit -m "feat: add input focus result contract"
```

---

### Task 5: Add Windows Perception Bridge

**Files:**
- Create: `app/desktop/windows_adapter/perception_bridge.py`
- Test: `tests/desktop/windows_adapter/test_perception_bridge.py`

**Step 1: Write the failing tests**

Create `tests/desktop/windows_adapter/test_perception_bridge.py`:

```python
from app.desktop.perception.jd_workspace_parser import parse_jd_workspace
from app.desktop.perception.region_classifier import classify_regions
from app.desktop.windows_adapter.foreground_window import build_foreground_window_result
from app.desktop.windows_adapter.input_focus import build_focus_result
from app.desktop.windows_adapter.perception_bridge import build_windows_perception_result


def test_build_windows_perception_result_keeps_desktop_context_and_focus_result():
    probe_result = build_foreground_window_result(
        handle=1001,
        title="evw10158991",
        process_name="jd-workbench.exe",
        bounds=[0, 0, 1680, 1048],
        is_foreground=True,
    )
    regions = classify_regions([
        {"region_hint": "chat", "text": "这款还有吗？", "message_role": "customer"},
        {"region_hint": "input", "editable": True, "has_smart_reply": True, "existing_text": ""},
        {"region_hint": "send_button", "visible": True},
    ])["regions"]
    desktop_context = parse_jd_workspace(
        regions,
        active_customer={"id": "jd_4a3d4c80e30ef", "name": "jd_4a3d4c80e30ef"},
        confidence=0.9,
    )
    focus_result = build_focus_result(
        focused=True,
        target_role="edit",
        target_name="输入框",
        reason="",
    )

    result = build_windows_perception_result(
        probe_result=probe_result,
        desktop_context=desktop_context,
        focus_result=focus_result,
    )

    assert result["ok"] is True
    assert result["probe_result"]["handle"] == 1001
    assert result["desktop_context"]["platform"] == "jd_customer_service"
    assert result["focus_result"]["focused"] is True
```

**Step 2: Run test to verify it fails**

Run:

```bash
py -3 -m pytest tests/desktop/windows_adapter/test_perception_bridge.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'app.desktop.windows_adapter.perception_bridge'`.

**Step 3: Write minimal implementation**

Create `app/desktop/windows_adapter/perception_bridge.py`:

```python
from __future__ import annotations


def build_windows_perception_result(
    *,
    probe_result: dict,
    desktop_context: dict,
    focus_result: dict,
) -> dict:
    return {
        "ok": True,
        "probe_result": probe_result,
        "desktop_context": desktop_context,
        "focus_result": focus_result,
    }
```

**Step 4: Run test to verify it passes**

Run:

```bash
py -3 -m pytest tests/desktop/windows_adapter/test_perception_bridge.py -v
```

Expected: PASS.

**Step 5: Run full tests**

Run:

```bash
py -3 -m pytest tests
```

Expected: PASS.

**Step 6: Commit**

```bash
git add app/desktop/windows_adapter/perception_bridge.py tests/desktop/windows_adapter/test_perception_bridge.py
git commit -m "feat: add windows perception bridge contract"
```

---

### Task 6: Add Windows Adapter to Perception Pipeline Contract Test

**Files:**
- Create: `tests/desktop/windows_adapter/test_windows_adapter_pipeline.py`
- Modify: `app/desktop/windows_adapter/perception_bridge.py` (only if needed)

**Step 1: Write the failing test**

Create `tests/desktop/windows_adapter/test_windows_adapter_pipeline.py`:

```python
from app.desktop.launcher import launch_desktop_assistant
from app.desktop.perception.jd_workspace_parser import parse_jd_workspace
from app.desktop.perception.region_classifier import classify_regions
from app.desktop.windows_adapter.foreground_window import build_foreground_window_result
from app.desktop.windows_adapter.input_focus import build_focus_result
from app.desktop.windows_adapter.perception_bridge import build_windows_perception_result


def test_windows_adapter_pipeline_keeps_manual_send_boundary():
    probe_result = build_foreground_window_result(
        handle=1001,
        title="evw10158991",
        process_name="jd-workbench.exe",
        bounds=[0, 0, 1680, 1048],
        is_foreground=True,
    )
    regions = classify_regions([
        {"region_hint": "chat", "text": "这款还有吗？", "message_role": "customer"},
        {"region_hint": "product", "title": "台式电脑主机", "sku": "10017775551", "stock_status": "无货"},
        {"region_hint": "input", "editable": True, "has_smart_reply": True, "existing_text": ""},
        {"region_hint": "send_button", "visible": True},
    ])["regions"]
    desktop_context = parse_jd_workspace(
        regions,
        active_customer={"id": "jd_4a3d4c80e30ef", "name": "jd_4a3d4c80e30ef"},
        confidence=0.9,
    )
    focus_result = build_focus_result(
        focused=True,
        target_role="edit",
        target_name="输入框",
        reason="",
    )
    bridge_result = build_windows_perception_result(
        probe_result=probe_result,
        desktop_context=desktop_context,
        focus_result=focus_result,
    )

    launch_result = launch_desktop_assistant(
        command="京东客服启动",
        desktop_context=bridge_result["desktop_context"],
        shop_id="shop_001",
        session_id="desktop-session-1",
    )

    assert launch_result["ok"] is True
    assert bridge_result["focus_result"]["focused"] is True
    assert launch_result["fill_action"]["auto_send_allowed"] is False
    assert launch_result["fill_action"]["send_policy"] == "manual_only"
```

**Step 2: Run test to verify it fails if integration is incomplete**

Run:

```bash
py -3 -m pytest tests/desktop/windows_adapter/test_windows_adapter_pipeline.py -v
```

Expected: FAIL only if bridge contracts are insufficient.

**Step 3: Make minimal integration fixes if needed**

Only if the test fails, make the smallest change required. Do not add fill/send behavior.

**Step 4: Run test to verify it passes**

Run:

```bash
py -3 -m pytest tests/desktop/windows_adapter/test_windows_adapter_pipeline.py -v
```

Expected: PASS.

**Step 5: Run full tests**

Run:

```bash
py -3 -m pytest tests
```

Expected: PASS.

**Step 6: Commit**

```bash
git add tests/desktop/windows_adapter/test_windows_adapter_pipeline.py app/desktop/windows_adapter/perception_bridge.py
git commit -m "feat: connect windows adapter pipeline to launcher"
```

---

### Task 7: Update Docs for Windows Adapter Entry

**Files:**
- Modify: `docs/windows-ui-automation-adapter-direction.md`
- Modify: `CLAUDE.md`
- Test: manual doc review

**Step 1: Update direction doc**

Add an `Implementation Entry` section stating that the first Windows adapter implementation starts from structured foreground-window results and normalized automation nodes, not a live automation API call yet.

Suggested text:

```markdown
## Implementation Entry

The first Windows UI Automation adapter implementation starts from structured foreground-window results, normalized automation nodes, and explicit focus-result contracts. It does not yet call a live Windows automation backend directly.

This keeps the adapter layer deterministic and testable while preserving the long-term architecture: a real Windows automation backend can later feed `windows_window_probe`, `windows_ui_tree_adapter`, and `windows_input_focus` without changing the downstream bridge and launcher contracts.
```

**Step 2: Update CLAUDE.md**

Add to key code paths:

- `app/desktop/windows_adapter/foreground_window.py`
- `app/desktop/windows_adapter/ui_node_adapter.py`
- `app/desktop/windows_adapter/region_input_bridge.py`
- `app/desktop/windows_adapter/input_focus.py`
- `app/desktop/windows_adapter/perception_bridge.py`

Add a boundary note that the Windows adapter currently starts from structured adapter inputs and does not yet call a live Windows UI Automation backend.

**Step 3: Run full tests**

Run:

```bash
py -3 -m pytest tests
```

Expected: PASS.

**Step 4: Review docs manually**

Confirm:

- Docs still state no fill/send happens in this stage.
- Docs do not falsely claim a live Windows automation backend already exists.
- Docs keep focus separate from fill/send actions.

**Step 5: Commit**

```bash
git add docs/windows-ui-automation-adapter-direction.md CLAUDE.md
git commit -m "docs: document windows adapter implementation entry"
```

---

## Final Verification

After all tasks are complete, run:

```bash
py -3 -m pytest tests
```

Expected: all tests pass.

Then run a smoke check in Python that proves:

- a Windows adapter bridge result contains `desktop_context` and `focus_result`
- `desktop_context` can be passed into `launch_desktop_assistant(...)`
- the final `fill_action.auto_send_allowed` remains `false`

Do not claim completion unless both the full test suite and the adapter-to-launcher smoke check have been run fresh and their output confirms success.
