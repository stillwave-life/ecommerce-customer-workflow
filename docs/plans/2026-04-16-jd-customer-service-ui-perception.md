# JD Customer Service UI Perception Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build the first real UI perception pipeline that converts JD customer-service workspace signals into standard `desktop_context` objects consumable by the existing Phase A launcher/reply/fill chain.

**Architecture:** Add a new `app/desktop/perception/` package that separates window probing, raw UI node reading, region classification, JD workspace parsing, and OCR fallback contracts. The first implementation remains deterministic and test-driven: it works from structured probe/node inputs rather than directly capturing the live UI, so the real Windows UI Automation adapter can be added later without rewriting the parsing pipeline.

**Tech Stack:** Python, pytest, existing `app/desktop` contracts, JSON-style script entrypoints, local worktree development.

---

## Context and Constraints

Read these files before implementation:

- `docs/jd-customer-service-ui-perception-direction.md`
- `docs/jd-customer-service-desktop-agent-direction.md`
- `docs/plans/2026-04-16-jd-customer-service-desktop-agent-phase-a.md`
- `app/desktop/context.py`
- `app/desktop/launcher.py`
- `scripts/jd_customer_service_start.py`

Hard constraints:

- Do not implement automatic sending.
- Do not implement direct screen capture as the primary Phase B logic.
- Do not bypass the existing `desktop_context -> launcher -> prepare_mapper -> reply_composer -> fill_action` chain.
- Keep UI perception separate from reply generation and fill actions.
- UI Automation / Accessibility remains the primary route; OCR is contract-only fallback for now.
- The first implementation must be testable without a live JD backend window.

Recommended verification command after each task:

```bash
py -3 -m pytest tests
```

If `py -3` is unavailable, use:

```bash
python3 -m pytest tests
```

---

### Task 1: Add Window Probe Contract

**Files:**
- Create: `app/desktop/perception/__init__.py`
- Create: `app/desktop/perception/window_probe.py`
- Test: `tests/desktop/perception/test_window_probe.py`

**Step 1: Write the failing test**

Create `tests/desktop/perception/test_window_probe.py`:

```python
from app.desktop.perception.window_probe import build_window_probe_result


def test_build_window_probe_result_marks_jd_candidate_window():
    result = build_window_probe_result(
        window_title="evw10158991",
        process_name="jd-workbench.exe",
        window_bounds=[0, 0, 1680, 1048],
        is_foreground=True,
        platform_hint="jd_customer_service",
        confidence=0.82,
    )

    assert result["ok"] is True
    assert result["window_title"] == "evw10158991"
    assert result["platform_hint"] == "jd_customer_service"
    assert result["confidence"] == 0.82
```

**Step 2: Run test to verify it fails**

Run:

```bash
py -3 -m pytest tests/desktop/perception/test_window_probe.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'app.desktop.perception.window_probe'`.

**Step 3: Write minimal implementation**

Create `app/desktop/perception/__init__.py` as an empty package file.

Create `app/desktop/perception/window_probe.py`:

```python
from __future__ import annotations


def build_window_probe_result(
    *,
    window_title: str,
    process_name: str,
    window_bounds: list[int],
    is_foreground: bool,
    platform_hint: str,
    confidence: float,
) -> dict:
    return {
        "ok": True,
        "window_title": window_title,
        "process_name": process_name,
        "window_bounds": list(window_bounds),
        "is_foreground": is_foreground,
        "platform_hint": platform_hint,
        "confidence": confidence,
    }
```

**Step 4: Run test to verify it passes**

Run:

```bash
py -3 -m pytest tests/desktop/perception/test_window_probe.py -v
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
git add app/desktop/perception/__init__.py app/desktop/perception/window_probe.py tests/desktop/perception/test_window_probe.py
git commit -m "feat: add window probe contract"
```

---

### Task 2: Add UI Tree Reader Contract

**Files:**
- Create: `app/desktop/perception/ui_tree_reader.py`
- Test: `tests/desktop/perception/test_ui_tree_reader.py`

**Step 1: Write the failing test**

Create `tests/desktop/perception/test_ui_tree_reader.py`:

```python
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
```

**Step 2: Run test to verify it fails**

Run:

```bash
py -3 -m pytest tests/desktop/perception/test_ui_tree_reader.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'app.desktop.perception.ui_tree_reader'`.

**Step 3: Write minimal implementation**

Create `app/desktop/perception/ui_tree_reader.py`:

```python
from __future__ import annotations

from typing import Any


def _copy_nodes(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [node.copy() for node in nodes]


def build_ui_tree_result(*, nodes: list[dict[str, Any]]) -> dict:
    return {
        "ok": True,
        "nodes": _copy_nodes(nodes),
    }
```

**Step 4: Run test to verify it passes**

Run:

```bash
py -3 -m pytest tests/desktop/perception/test_ui_tree_reader.py -v
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
git add app/desktop/perception/ui_tree_reader.py tests/desktop/perception/test_ui_tree_reader.py
git commit -m "feat: add ui tree reader contract"
```

---

### Task 3: Add Region Classifier

**Files:**
- Create: `app/desktop/perception/region_classifier.py`
- Test: `tests/desktop/perception/test_region_classifier.py`

**Step 1: Write the failing tests**

Create `tests/desktop/perception/test_region_classifier.py`:

```python
from app.desktop.perception.region_classifier import classify_regions


def test_classify_regions_splits_chat_product_user_input_nodes():
    nodes = [
        {"region_hint": "chat", "text": "这款还有吗？"},
        {"region_hint": "product", "text": "台式电脑主机"},
        {"region_hint": "user_order", "text": "近三个月订单"},
        {"region_hint": "input", "text": ""},
        {"region_hint": "send_button", "text": "发送(F1)"},
    ]

    result = classify_regions(nodes)

    assert result["ok"] is True
    assert len(result["regions"]["chat_region"]) == 1
    assert len(result["regions"]["product_region"]) == 1
    assert len(result["regions"]["user_order_region"]) == 1
    assert len(result["regions"]["input_region"]) == 1
    assert len(result["regions"]["send_button_region"]) == 1
```

**Step 2: Run test to verify it fails**

Run:

```bash
py -3 -m pytest tests/desktop/perception/test_region_classifier.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'app.desktop.perception.region_classifier'`.

**Step 3: Write minimal implementation**

Create `app/desktop/perception/region_classifier.py`:

```python
from __future__ import annotations

from typing import Any


REGION_MAP = {
    "conversation_list": "conversation_list_region",
    "chat": "chat_region",
    "product": "product_region",
    "user_order": "user_order_region",
    "input": "input_region",
    "send_button": "send_button_region",
}


def classify_regions(nodes: list[dict[str, Any]]) -> dict:
    regions = {value: [] for value in REGION_MAP.values()}
    for node in nodes:
        region_hint = str(node.get("region_hint", "")).strip()
        target = REGION_MAP.get(region_hint)
        if target:
            regions[target].append(node.copy())
    return {
        "ok": True,
        "regions": regions,
    }
```

**Step 4: Run test to verify it passes**

Run:

```bash
py -3 -m pytest tests/desktop/perception/test_region_classifier.py -v
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
git add app/desktop/perception/region_classifier.py tests/desktop/perception/test_region_classifier.py
git commit -m "feat: classify jd workspace regions"
```

---

### Task 4: Add JD Workspace Parser

**Files:**
- Create: `app/desktop/perception/jd_workspace_parser.py`
- Test: `tests/desktop/perception/test_jd_workspace_parser.py`

**Step 1: Write the failing tests**

Create `tests/desktop/perception/test_jd_workspace_parser.py`:

```python
from app.desktop.perception.jd_workspace_parser import parse_jd_workspace


def test_parse_jd_workspace_builds_desktop_context_from_regions():
    regions = {
        "chat_region": [{"text": "这款还有吗？", "message_role": "customer"}],
        "product_region": [{"title": "台式电脑主机", "sku": "10017775551", "stock_status": "无货"}],
        "user_order_region": [{"label": "PLUS"}, {"order_summary": "近三个月无订单"}],
        "input_region": [{"editable": True, "has_smart_reply": True, "existing_text": ""}],
        "send_button_region": [{"visible": True}],
        "conversation_list_region": [],
    }

    result = parse_jd_workspace(
        regions,
        active_customer={"id": "jd_4a3d4c80e30ef", "name": "jd_4a3d4c80e30ef"},
        confidence=0.91,
    )

    assert result["platform"] == "jd_customer_service"
    assert result["active_customer"]["id"] == "jd_4a3d4c80e30ef"
    assert result["chat_context"]["latest_customer_message"] == "这款还有吗？"
    assert result["product_context"]["items"][0]["sku"] == "10017775551"
    assert result["user_order_context"]["user_labels"] == ["PLUS"]
    assert result["input_context"]["editable"] is True
    assert result["input_context"]["send_button_visible"] is True
```

**Step 2: Run test to verify it fails**

Run:

```bash
py -3 -m pytest tests/desktop/perception/test_jd_workspace_parser.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'app.desktop.perception.jd_workspace_parser'`.

**Step 3: Write minimal implementation**

Create `app/desktop/perception/jd_workspace_parser.py`:

```python
from __future__ import annotations

from typing import Any

from app.desktop.context import (
    build_chat_context,
    build_desktop_context,
    build_input_context,
    build_product_context,
    build_user_order_context,
)


def _latest_customer_message(chat_region: list[dict[str, Any]]) -> str:
    for item in chat_region:
        if item.get("message_role") == "customer":
            return str(item.get("text", "")).strip()
    return ""


def _product_items(product_region: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [item.copy() for item in product_region if item.get("title") or item.get("sku")]


def _user_labels(user_order_region: list[dict[str, Any]]) -> list[str]:
    return [str(item.get("label", "")).strip() for item in user_order_region if str(item.get("label", "")).strip()]


def _orders(user_order_region: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{"summary": str(item.get("order_summary", "")).strip()} for item in user_order_region if str(item.get("order_summary", "")).strip()]


def parse_jd_workspace(
    regions: dict[str, list[dict[str, Any]]],
    *,
    active_customer: dict[str, str],
    confidence: float,
) -> dict:
    input_region = regions.get("input_region", [])
    send_button_region = regions.get("send_button_region", [])
    first_input = input_region[0] if input_region else {}

    return build_desktop_context(
        platform="jd_customer_service",
        confidence=confidence,
        active_customer=active_customer,
        chat_context=build_chat_context(
            latest_customer_message=_latest_customer_message(regions.get("chat_region", [])),
            recent_messages=[item.copy() for item in regions.get("chat_region", [])],
            contains_image=any(bool(item.get("contains_image")) for item in regions.get("chat_region", [])),
        ),
        product_context=build_product_context(
            tab_active=bool(regions.get("product_region")),
            items=_product_items(regions.get("product_region", [])),
        ),
        user_order_context=build_user_order_context(
            user_labels=_user_labels(regions.get("user_order_region", [])),
            orders=_orders(regions.get("user_order_region", [])),
            service_forms=[],
        ),
        input_context=build_input_context(
            editable=bool(first_input.get("editable")),
            has_smart_reply=bool(first_input.get("has_smart_reply")),
            send_button_visible=any(bool(item.get("visible")) for item in send_button_region),
            existing_text=str(first_input.get("existing_text", "")),
        ),
    )
```

**Step 4: Run test to verify it passes**

Run:

```bash
py -3 -m pytest tests/desktop/perception/test_jd_workspace_parser.py -v
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
git add app/desktop/perception/jd_workspace_parser.py tests/desktop/perception/test_jd_workspace_parser.py
git commit -m "feat: parse jd workspace regions into desktop context"
```

---

### Task 5: Add OCR Fallback Contract

**Files:**
- Create: `app/desktop/perception/ocr_fallback.py`
- Test: `tests/desktop/perception/test_ocr_fallback.py`

**Step 1: Write the failing test**

Create `tests/desktop/perception/test_ocr_fallback.py`:

```python
from app.desktop.perception.ocr_fallback import build_ocr_fallback_request


def test_build_ocr_fallback_request_tracks_missing_fields_and_regions():
    request = build_ocr_fallback_request(
        missing_fields=["latest_customer_message", "product_title"],
        screenshot_path="tmp/jd_workspace.png",
        region_names=["chat_region", "product_region"],
    )

    assert request["ok"] is True
    assert request["missing_fields"] == ["latest_customer_message", "product_title"]
    assert request["region_names"] == ["chat_region", "product_region"]
    assert request["screenshot_path"] == "tmp/jd_workspace.png"
```

**Step 2: Run test to verify it fails**

Run:

```bash
py -3 -m pytest tests/desktop/perception/test_ocr_fallback.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'app.desktop.perception.ocr_fallback'`.

**Step 3: Write minimal implementation**

Create `app/desktop/perception/ocr_fallback.py`:

```python
from __future__ import annotations


def build_ocr_fallback_request(
    *,
    missing_fields: list[str],
    screenshot_path: str,
    region_names: list[str],
) -> dict:
    return {
        "ok": True,
        "missing_fields": list(missing_fields),
        "screenshot_path": screenshot_path,
        "region_names": list(region_names),
    }
```

**Step 4: Run test to verify it passes**

Run:

```bash
py -3 -m pytest tests/desktop/perception/test_ocr_fallback.py -v
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
git add app/desktop/perception/ocr_fallback.py tests/desktop/perception/test_ocr_fallback.py
git commit -m "feat: add ocr fallback contract"
```

---

### Task 6: Add Perception-to-Launcher Contract Test

**Files:**
- Create: `tests/desktop/perception/test_perception_pipeline.py`
- Modify: `scripts/jd_customer_service_start.py`
- Modify: `app/desktop/launcher.py`

**Step 1: Write the failing test**

Create `tests/desktop/perception/test_perception_pipeline.py`:

```python
from app.desktop.launcher import launch_desktop_assistant
from app.desktop.perception.jd_workspace_parser import parse_jd_workspace


def test_perception_pipeline_outputs_launcher_consumable_desktop_context():
    regions = {
        "chat_region": [{"text": "这款还有吗？", "message_role": "customer"}],
        "product_region": [{"title": "台式电脑主机", "sku": "10017775551", "stock_status": "无货"}],
        "user_order_region": [{"label": "PLUS"}],
        "input_region": [{"editable": True, "has_smart_reply": True, "existing_text": ""}],
        "send_button_region": [{"visible": True}],
        "conversation_list_region": [],
    }

    desktop_context = parse_jd_workspace(
        regions,
        active_customer={"id": "jd_4a3d4c80e30ef", "name": "jd_4a3d4c80e30ef"},
        confidence=0.9,
    )

    result = launch_desktop_assistant(
        command="京东客服启动",
        desktop_context=desktop_context,
        shop_id="shop_001",
        session_id="desktop-session-1",
    )

    assert result["ok"] is True
    assert result["reply"]["prepared"]["product_ref"] == {"type": "sku", "value": "10017775551"}
    assert result["fill_action"]["send_policy"] == "manual_only"
```

**Step 2: Run test to verify it fails if parser output is insufficient**

Run:

```bash
py -3 -m pytest tests/desktop/perception/test_perception_pipeline.py -v
```

Expected: FAIL if parser/launcher integration is incomplete.

**Step 3: Make minimal integration fixes if needed**

Only if the test fails, make the smallest change required in `app/desktop/launcher.py` or `scripts/jd_customer_service_start.py` to preserve contract compatibility. Do not add new behavior beyond what the test proves.

**Step 4: Run test to verify it passes**

Run:

```bash
py -3 -m pytest tests/desktop/perception/test_perception_pipeline.py -v
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
git add tests/desktop/perception/test_perception_pipeline.py app/desktop/launcher.py scripts/jd_customer_service_start.py
git commit -m "feat: connect perception pipeline to launcher contract"
```

---

### Task 7: Update Docs for UI Perception Entry

**Files:**
- Modify: `docs/jd-customer-service-ui-perception-direction.md`
- Modify: `CLAUDE.md`
- Test: manual doc review

**Step 1: Update direction doc**

Add a short `Implementation Entry` section stating that the first implementation starts from synthetic probe/tree/region inputs and does not yet connect to a live Windows UI Automation backend.

Suggested text:

```markdown
## Implementation Entry

The first implementation of the UI perception layer starts from structured probe results, UI node lists, and classified region inputs. It does not yet capture a live Windows UI Automation tree directly.

This keeps the pipeline deterministic and testable while preserving the intended long-term architecture: a real Windows UI Automation adapter can later feed `window_probe`, `ui_tree_reader`, and `region_classifier` without changing the downstream `jd_workspace_parser -> desktop_context -> launcher` contract.
```

**Step 2: Update CLAUDE.md**

Add to key code paths:

- `app/desktop/perception/window_probe.py`
- `app/desktop/perception/ui_tree_reader.py`
- `app/desktop/perception/region_classifier.py`
- `app/desktop/perception/jd_workspace_parser.py`
- `app/desktop/perception/ocr_fallback.py`

Add a boundary note that UI perception currently starts from structured probe/node inputs, not a live Windows automation backend.

**Step 3: Run full tests**

Run:

```bash
py -3 -m pytest tests
```

Expected: PASS.

**Step 4: Review docs manually**

Confirm:

- Docs still state UI Automation is the primary intended route.
- Docs do not falsely claim live Windows automation is already implemented.
- Docs preserve the manual-send-only boundary.

**Step 5: Commit**

```bash
git add docs/jd-customer-service-ui-perception-direction.md CLAUDE.md
git commit -m "docs: document ui perception implementation entry"
```

---

## Final Verification

After all tasks are complete, run:

```bash
py -3 -m pytest tests
```

Expected: all tests pass.

Then run a smoke check in Python REPL or a one-shot command that proves `parse_jd_workspace(...)` produces a `desktop_context` accepted by `launch_desktop_assistant(...)` and still returns `fill_action.auto_send_allowed = false`.

Do not claim completion unless both the full test suite and the perception-to-launcher smoke check have been run fresh and their output confirms success.
