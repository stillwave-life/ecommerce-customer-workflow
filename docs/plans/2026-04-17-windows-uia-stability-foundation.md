# Windows UIA Stability Foundation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a stable, diagnosable Windows UIA foundation that can inspect the real foreground JD workspace, score input-box candidates, gate risky actions, and validate focus behavior before any future text-fill integration.

**Architecture:** Add a new `app/desktop/windows_uia_foundation/` package that sits below the existing Windows adapter contracts and above future live UIA backend calls. This foundation layer is responsible for diagnostics, candidate scoring, action gating, and focus verification; it does not write text or send messages.

**Tech Stack:** Python, pytest, existing `app/desktop/windows_adapter` contracts, existing `app/desktop/perception` pipeline, JSON-style diagnostic outputs.

---

## Context and Constraints

Read these files before implementation:

- `docs/windows-uia-stability-foundation.md`
- `docs/windows-ui-automation-adapter-direction.md`
- `docs/plans/2026-04-16-windows-ui-automation-adapter.md`
- `app/desktop/windows_adapter/foreground_window.py`
- `app/desktop/windows_adapter/ui_node_adapter.py`
- `app/desktop/windows_adapter/region_input_bridge.py`
- `app/desktop/windows_adapter/input_focus.py`
- `app/desktop/windows_adapter/perception_bridge.py`
- `app/desktop/launcher.py`

Hard constraints:

- Do not implement text fill.
- Do not implement send actions.
- Do not bypass action gating.
- Keep diagnostics separate from reply generation.
- Keep candidate scoring separate from focus execution.
- Focus behavior must remain independently verifiable.
- The first implementation may still use structured adapter inputs, but every output must be designed for future real UIA backend integration.

Recommended verification command after each task:

```bash
py -3 -m pytest tests
```

If `py -3` is unavailable, use:

```bash
python3 -m pytest tests
```

---

### Task 1: Add UIA Probe Diagnostics Contract

**Files:**
- Create: `app/desktop/windows_uia_foundation/__init__.py`
- Create: `app/desktop/windows_uia_foundation/probe_diagnostics.py`
- Test: `tests/desktop/windows_uia_foundation/test_probe_diagnostics.py`

**Step 1: Write the failing test**

Create `tests/desktop/windows_uia_foundation/test_probe_diagnostics.py`:

```python
from app.desktop.windows_uia_foundation.probe_diagnostics import build_probe_diagnostics


def test_build_probe_diagnostics_summarizes_node_counts():
    diagnostics = build_probe_diagnostics(
        window={"title": "evw10158991", "handle": 1001},
        node_count=423,
        editable_node_count=3,
        clickable_node_count=27,
        visible_node_count=390,
    )

    assert diagnostics["ok"] is True
    assert diagnostics["window"]["title"] == "evw10158991"
    assert diagnostics["node_stats"]["node_count"] == 423
    assert diagnostics["node_stats"]["editable_node_count"] == 3
    assert diagnostics["node_stats"]["clickable_node_count"] == 27
    assert diagnostics["node_stats"]["visible_node_count"] == 390
```

**Step 2: Run test to verify it fails**

Run:

```bash
py -3 -m pytest tests/desktop/windows_uia_foundation/test_probe_diagnostics.py -v
```

Expected: FAIL with `ModuleNotFoundError` for `app.desktop.windows_uia_foundation.probe_diagnostics`.

**Step 3: Write minimal implementation**

Create `app/desktop/windows_uia_foundation/__init__.py` as an empty package file.

Create `app/desktop/windows_uia_foundation/probe_diagnostics.py`:

```python
from __future__ import annotations


def build_probe_diagnostics(
    *,
    window: dict,
    node_count: int,
    editable_node_count: int,
    clickable_node_count: int,
    visible_node_count: int,
) -> dict:
    return {
        "ok": True,
        "window": window.copy(),
        "node_stats": {
            "node_count": node_count,
            "editable_node_count": editable_node_count,
            "clickable_node_count": clickable_node_count,
            "visible_node_count": visible_node_count,
        },
    }
```

**Step 4: Run test to verify it passes**

Run:

```bash
py -3 -m pytest tests/desktop/windows_uia_foundation/test_probe_diagnostics.py -v
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
git add app/desktop/windows_uia_foundation/__init__.py app/desktop/windows_uia_foundation/probe_diagnostics.py tests/desktop/windows_uia_foundation/test_probe_diagnostics.py
git commit -m "feat: add uia probe diagnostics contract"
```

---

### Task 2: Add Input Candidate Ranker

**Files:**
- Create: `app/desktop/windows_uia_foundation/input_candidate_ranker.py`
- Test: `tests/desktop/windows_uia_foundation/test_input_candidate_ranker.py`

**Step 1: Write the failing test**

Create `tests/desktop/windows_uia_foundation/test_input_candidate_ranker.py`:

```python
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
```

**Step 2: Run test to verify it fails**

Run:

```bash
py -3 -m pytest tests/desktop/windows_uia_foundation/test_input_candidate_ranker.py -v
```

Expected: FAIL with `ModuleNotFoundError` for `app.desktop.windows_uia_foundation.input_candidate_ranker`.

**Step 3: Write minimal implementation**

Create `app/desktop/windows_uia_foundation/input_candidate_ranker.py`:

```python
from __future__ import annotations

from typing import Any


def _score_node(node: dict[str, Any]) -> tuple[float, list[str]]:
    score = 0.0
    reasons: list[str] = []

    if node.get("editable"):
        score += 0.4
        reasons.append("editable")

    bounds = node.get("bounds") or [0, 0, 0, 0]
    top = bounds[1] if len(bounds) >= 2 else 0
    bottom = bounds[3] if len(bounds) >= 4 else 0
    height = max(0, bottom - top)

    if top >= 600:
        score += 0.3
        reasons.append("bottom_region")

    if height >= 200:
        score += 0.2
        reasons.append("large_text_area")

    name = str(node.get("name", "")).strip()
    if "搜索" in name:
        score -= 0.2
        reasons.append("search_penalty")

    return score, reasons


def rank_input_candidates(nodes: list[dict[str, Any]]) -> dict:
    candidates = []
    for node in nodes:
        score, reasons = _score_node(node)
        candidates.append({"node": node.copy(), "score": score, "reasons": reasons})
    candidates.sort(key=lambda item: item["score"], reverse=True)
    return {"ok": True, "candidates": candidates}
```

**Step 4: Run test to verify it passes**

Run:

```bash
py -3 -m pytest tests/desktop/windows_uia_foundation/test_input_candidate_ranker.py -v
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
git add app/desktop/windows_uia_foundation/input_candidate_ranker.py tests/desktop/windows_uia_foundation/test_input_candidate_ranker.py
git commit -m "feat: rank input candidates for uia focus"
```

---

### Task 3: Add Action Gate

**Files:**
- Create: `app/desktop/windows_uia_foundation/action_gate.py`
- Test: `tests/desktop/windows_uia_foundation/test_action_gate.py`

**Step 1: Write the failing tests**

Create `tests/desktop/windows_uia_foundation/test_action_gate.py`:

```python
from app.desktop.windows_uia_foundation.action_gate import build_action_gate_result


def test_build_action_gate_result_allows_focus_for_high_score():
    result = build_action_gate_result(score=0.86, candidate_count=1)

    assert result["decision"] == "allow_focus"
    assert result["reason"] == "candidate_score_high_enough"


def test_build_action_gate_result_blocks_when_no_candidates():
    result = build_action_gate_result(score=0.0, candidate_count=0)

    assert result["decision"] == "block"
    assert result["reason"] == "no_input_candidates"


def test_build_action_gate_result_requests_manual_review_for_mid_score():
    result = build_action_gate_result(score=0.62, candidate_count=1)

    assert result["decision"] == "manual_review"
    assert result["reason"] == "candidate_score_uncertain"
```

**Step 2: Run test to verify it fails**

Run:

```bash
py -3 -m pytest tests/desktop/windows_uia_foundation/test_action_gate.py -v
```

Expected: FAIL with `ModuleNotFoundError` for `app.desktop.windows_uia_foundation.action_gate`.

**Step 3: Write minimal implementation**

Create `app/desktop/windows_uia_foundation/action_gate.py`:

```python
from __future__ import annotations


def build_action_gate_result(*, score: float, candidate_count: int) -> dict:
    if candidate_count == 0:
        return {"decision": "block", "reason": "no_input_candidates", "score": score}
    if score >= 0.8:
        return {"decision": "allow_focus", "reason": "candidate_score_high_enough", "score": score}
    if score >= 0.5:
        return {"decision": "manual_review", "reason": "candidate_score_uncertain", "score": score}
    return {"decision": "block", "reason": "candidate_score_too_low", "score": score}
```

**Step 4: Run test to verify it passes**

Run:

```bash
py -3 -m pytest tests/desktop/windows_uia_foundation/test_action_gate.py -v
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
git add app/desktop/windows_uia_foundation/action_gate.py tests/desktop/windows_uia_foundation/test_action_gate.py
git commit -m "feat: add uia action gate"
```

---

### Task 4: Add Focus Verification Contract

**Files:**
- Create: `app/desktop/windows_uia_foundation/focus_verifier.py`
- Test: `tests/desktop/windows_uia_foundation/test_focus_verifier.py`

**Step 1: Write the failing tests**

Create `tests/desktop/windows_uia_foundation/test_focus_verifier.py`:

```python
from app.desktop.windows_uia_foundation.focus_verifier import build_focus_verification


def test_build_focus_verification_reports_success():
    result = build_focus_verification(focused=True, target_name="输入框")

    assert result["ok"] is True
    assert result["focused"] is True
    assert result["target_name"] == "输入框"
    assert result["reason"] == ""


def test_build_focus_verification_reports_failure():
    result = build_focus_verification(focused=False, target_name="", reason="focus_verification_failed")

    assert result["ok"] is False
    assert result["focused"] is False
    assert result["reason"] == "focus_verification_failed"
```

**Step 2: Run test to verify it fails**

Run:

```bash
py -3 -m pytest tests/desktop/windows_uia_foundation/test_focus_verifier.py -v
```

Expected: FAIL with `ModuleNotFoundError` for `app.desktop.windows_uia_foundation.focus_verifier`.

**Step 3: Write minimal implementation**

Create `app/desktop/windows_uia_foundation/focus_verifier.py`:

```python
from __future__ import annotations


def build_focus_verification(*, focused: bool, target_name: str, reason: str = "") -> dict:
    return {
        "ok": focused,
        "focused": focused,
        "target_name": target_name,
        "reason": reason,
    }
```

**Step 4: Run test to verify it passes**

Run:

```bash
py -3 -m pytest tests/desktop/windows_uia_foundation/test_focus_verifier.py -v
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
git add app/desktop/windows_uia_foundation/focus_verifier.py tests/desktop/windows_uia_foundation/test_focus_verifier.py
git commit -m "feat: add focus verification contract"
```

---

### Task 5: Add Diagnostics Report Aggregator

**Files:**
- Create: `app/desktop/windows_uia_foundation/diagnostics_report.py`
- Test: `tests/desktop/windows_uia_foundation/test_diagnostics_report.py`

**Step 1: Write the failing test**

Create `tests/desktop/windows_uia_foundation/test_diagnostics_report.py`:

```python
from app.desktop.windows_uia_foundation.diagnostics_report import build_diagnostics_report


def test_build_diagnostics_report_aggregates_probe_candidates_gate_and_focus():
    report = build_diagnostics_report(
        window={"title": "evw10158991"},
        node_stats={"node_count": 423},
        input_candidates=[{"score": 0.86}],
        gate_result={"decision": "allow_focus"},
        focus_result={"focused": True},
        desktop_context={"platform": "jd_customer_service"},
    )

    assert report["window"]["title"] == "evw10158991"
    assert report["node_stats"]["node_count"] == 423
    assert report["input_candidates"][0]["score"] == 0.86
    assert report["gate_result"]["decision"] == "allow_focus"
    assert report["focus_result"]["focused"] is True
    assert report["desktop_context"]["platform"] == "jd_customer_service"
```

**Step 2: Run test to verify it fails**

Run:

```bash
py -3 -m pytest tests/desktop/windows_uia_foundation/test_diagnostics_report.py -v
```

Expected: FAIL with `ModuleNotFoundError` for `app.desktop.windows_uia_foundation.diagnostics_report`.

**Step 3: Write minimal implementation**

Create `app/desktop/windows_uia_foundation/diagnostics_report.py`:

```python
from __future__ import annotations


def build_diagnostics_report(
    *,
    window: dict,
    node_stats: dict,
    input_candidates: list[dict],
    gate_result: dict,
    focus_result: dict,
    desktop_context: dict,
) -> dict:
    return {
        "window": window.copy(),
        "node_stats": node_stats.copy(),
        "input_candidates": [item.copy() for item in input_candidates],
        "gate_result": gate_result.copy(),
        "focus_result": focus_result.copy(),
        "desktop_context": desktop_context.copy(),
    }
```

**Step 4: Run test to verify it passes**

Run:

```bash
py -3 -m pytest tests/desktop/windows_uia_foundation/test_diagnostics_report.py -v
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
git add app/desktop/windows_uia_foundation/diagnostics_report.py tests/desktop/windows_uia_foundation/test_diagnostics_report.py
git commit -m "feat: add uia diagnostics report aggregator"
```

---

### Task 6: Add Foundation-to-Launcher Contract Test

**Files:**
- Create: `tests/desktop/windows_uia_foundation/test_foundation_pipeline.py`

**Step 1: Write the failing test**

Create `tests/desktop/windows_uia_foundation/test_foundation_pipeline.py`:

```python
from app.desktop.launcher import launch_desktop_assistant
from app.desktop.perception.jd_workspace_parser import parse_jd_workspace
from app.desktop.perception.region_classifier import classify_regions
from app.desktop.windows_uia_foundation.action_gate import build_action_gate_result
from app.desktop.windows_uia_foundation.diagnostics_report import build_diagnostics_report
from app.desktop.windows_uia_foundation.focus_verifier import build_focus_verification
from app.desktop.windows_uia_foundation.input_candidate_ranker import rank_input_candidates
from app.desktop.windows_uia_foundation.probe_diagnostics import build_probe_diagnostics


def test_uia_foundation_pipeline_preserves_manual_send_boundary():
    nodes = [
        {"role": "edit", "name": "输入框", "bounds": [360, 690, 970, 1010], "editable": True, "clickable": True, "visible": True, "region_hint": "input", "has_smart_reply": True, "existing_text": ""},
        {"role": "text", "name": "客户消息", "text": "这款还有吗？", "region_hint": "chat", "message_role": "customer"},
        {"role": "button", "name": "发送(F1)", "visible": True, "region_hint": "send_button"},
    ]

    probe = build_probe_diagnostics(
        window={"title": "evw10158991", "handle": 1001},
        node_count=3,
        editable_node_count=1,
        clickable_node_count=2,
        visible_node_count=3,
    )
    ranked = rank_input_candidates(nodes)
    gate = build_action_gate_result(score=ranked["candidates"][0]["score"], candidate_count=len(ranked["candidates"]))
    focus = build_focus_verification(focused=True, target_name="输入框")
    regions = classify_regions(nodes)["regions"]
    desktop_context = parse_jd_workspace(
        regions,
        active_customer={"id": "jd_4a3d4c80e30ef", "name": "jd_4a3d4c80e30ef"},
        confidence=0.9,
    )
    report = build_diagnostics_report(
        window=probe["window"],
        node_stats=probe["node_stats"],
        input_candidates=ranked["candidates"],
        gate_result=gate,
        focus_result=focus,
        desktop_context=desktop_context,
    )

    launch_result = launch_desktop_assistant(
        command="京东客服启动",
        desktop_context=report["desktop_context"],
        shop_id="shop_001",
        session_id="desktop-session-1",
    )

    assert launch_result["ok"] is True
    assert gate["decision"] == "allow_focus"
    assert focus["focused"] is True
    assert launch_result["fill_action"]["auto_send_allowed"] is False
    assert launch_result["fill_action"]["send_policy"] == "manual_only"
```

**Step 2: Run test to verify it fails if foundation contracts are incomplete**

Run:

```bash
py -3 -m pytest tests/desktop/windows_uia_foundation/test_foundation_pipeline.py -v
```

Expected: FAIL only if a foundation contract is missing or incompatible.

**Step 3: Make minimal fixes only if needed**

If the test fails, make the smallest change necessary. Do not add text fill or send behavior.

**Step 4: Run test to verify it passes**

Run:

```bash
py -3 -m pytest tests/desktop/windows_uia_foundation/test_foundation_pipeline.py -v
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
git add tests/desktop/windows_uia_foundation/test_foundation_pipeline.py
git commit -m "feat: connect uia foundation pipeline to launcher"
```

---

### Task 7: Update Docs for UIA Stability Foundation Entry

**Files:**
- Modify: `docs/windows-uia-stability-foundation.md`
- Modify: `CLAUDE.md`
- Test: manual doc review

**Step 1: Update direction doc**

Add an `Implementation Entry` section stating that the first UIA stability foundation implementation starts from structured probe inputs, normalized nodes, and explicit diagnostics / gate / focus contracts, not direct text fill.

Suggested text:

```markdown
## Implementation Entry

The first Windows UIA stability foundation implementation starts from structured probe inputs, normalized nodes, candidate scores, action-gate results, and focus verification contracts. It does not yet perform real text fill.

This keeps the foundation highly observable and testable while preserving the long-term architecture: once the real backend is proven stable, text-fill logic can be added on top of the same diagnostics, gate, and verification layers rather than replacing them.
```

**Step 2: Update CLAUDE.md**

Add to key code paths:

- `app/desktop/windows_uia_foundation/probe_diagnostics.py`
- `app/desktop/windows_uia_foundation/input_candidate_ranker.py`
- `app/desktop/windows_uia_foundation/action_gate.py`
- `app/desktop/windows_uia_foundation/focus_verifier.py`
- `app/desktop/windows_uia_foundation/diagnostics_report.py`

Add a boundary note that the UIA foundation currently supports diagnostics, candidate scoring, action gating, and focus verification — not real text fill.

**Step 3: Run full tests**

Run:

```bash
py -3 -m pytest tests
```

Expected: PASS.

**Step 4: Review docs manually**

Confirm:

- Docs still state no text fill and no send in this stage.
- Docs clearly explain why diagnostics/gating come before write actions.
- Docs keep future fill capability as a later stage, not current reality.

**Step 5: Commit**

```bash
git add docs/windows-uia-stability-foundation.md CLAUDE.md
git commit -m "docs: document uia stability foundation entry"
```

---

## Final Verification

After all tasks are complete, run:

```bash
py -3 -m pytest tests
```

Expected: all tests pass.

Then run a smoke check in Python that proves:

- node diagnostics can be produced
- input candidates can be ranked
- gate decision can allow focus
- focus verification can succeed
- the resulting `desktop_context` still flows through `launch_desktop_assistant(...)`
- the final `fill_action.auto_send_allowed` remains `false`

Do not claim completion unless both the full test suite and the foundation-to-launcher smoke check have been run fresh and their output confirms success.
