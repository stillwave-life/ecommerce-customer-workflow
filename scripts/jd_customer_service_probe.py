from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.desktop.perception.jd_workspace_parser import parse_jd_workspace
from app.desktop.perception.region_classifier import classify_regions
from app.desktop.windows_adapter.foreground_window import build_foreground_window_result
from app.desktop.windows_adapter.input_focus import build_focus_result
from app.desktop.windows_adapter.live_backend import collect_live_uia_snapshot
from app.desktop.windows_adapter.perception_bridge import build_windows_perception_result
from app.desktop.windows_adapter.region_input_bridge import build_region_input_nodes
from app.desktop.windows_uia_foundation.action_gate import build_action_gate_result
from app.desktop.windows_uia_foundation.diagnostics_report import build_diagnostics_report
from app.desktop.windows_uia_foundation.input_candidate_ranker import rank_input_candidates
from app.desktop.windows_uia_foundation.probe_diagnostics import build_probe_diagnostics
from app.models import build_error_response


def configure_stdio() -> None:
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            reconfigure(encoding="utf-8")


def print_json(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False))


def _require_dict(payload: dict[str, Any], key: str) -> dict[str, Any] | None:
    value = payload.get(key)
    return value if isinstance(value, dict) else None


def _require_nodes(payload: dict[str, Any]) -> list[dict[str, Any]] | None:
    nodes = payload.get("nodes")
    if not isinstance(nodes, list) or not all(isinstance(item, dict) for item in nodes):
        return None
    return nodes


def _node_stats(nodes: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "node_count": len(nodes),
        "editable_node_count": sum(1 for node in nodes if node.get("editable")),
        "clickable_node_count": sum(1 for node in nodes if node.get("clickable")),
        "visible_node_count": sum(1 for node in nodes if node.get("visible", True)),
    }


def _backend_metadata(payload: dict[str, Any]) -> dict[str, Any]:
    backend = payload.get("backend")
    if isinstance(backend, dict):
        return {
            "type": str(backend.get("type", "windows_uia") or "windows_uia"),
            "live": bool(backend.get("live", False)),
        }
    return {"type": "windows_uia", "live": False}


def _snapshot_from_payload(payload: dict[str, Any], backend: dict[str, Any]) -> dict[str, Any]:
    if backend.get("live"):
        return collect_live_uia_snapshot()

    window = _require_dict(payload, "window")
    if window is None:
        return build_error_response("window is required")

    nodes = _require_nodes(payload)
    if nodes is None:
        return build_error_response("nodes must be a list of objects")

    return {
        "ok": True,
        "backend": backend,
        "window": window,
        "nodes": nodes,
    }


def build_probe_payload(payload: dict[str, Any]) -> dict[str, Any]:
    active_customer = _require_dict(payload, "active_customer") or {"id": "", "name": ""}
    confidence = float(payload.get("confidence", 0.9))
    backend = _backend_metadata(payload)
    snapshot = _snapshot_from_payload(payload, backend)
    if not snapshot.get("ok"):
        return snapshot

    window = snapshot["window"]
    nodes = snapshot["nodes"]
    backend = snapshot.get("backend", backend)

    probe_result = build_foreground_window_result(
        handle=int(window.get("handle", 0)),
        title=str(window.get("title", "")),
        process_name=str(window.get("process_name", "")),
        bounds=list(window.get("bounds", [0, 0, 0, 0])),
        is_foreground=bool(window.get("is_foreground", False)),
    )
    region_nodes = build_region_input_nodes(nodes)
    ranked = rank_input_candidates(region_nodes)
    top_candidate = ranked["candidates"][0] if ranked["candidates"] else {"score": 0.0, "node": {}}
    gate_result = build_action_gate_result(score=float(top_candidate["score"]), candidate_count=len(ranked["candidates"]))
    focus_allowed = gate_result["decision"] == "allow_focus"
    focus_result = build_focus_result(
        focused=focus_allowed,
        target_role=str(top_candidate.get("node", {}).get("role", "")) if focus_allowed else "",
        target_name=str(top_candidate.get("node", {}).get("name", "")) if focus_allowed else "",
        reason="" if focus_allowed else gate_result["reason"],
        target_bounds=top_candidate.get("node", {}).get("bounds") if focus_allowed else [],
        target_automation_id=str(top_candidate.get("node", {}).get("automation_id", "")) if focus_allowed else "",
    )
    regions = classify_regions(region_nodes)["regions"]
    desktop_context = parse_jd_workspace(regions, active_customer=active_customer, confidence=confidence)
    stats = _node_stats(region_nodes)
    probe_diagnostics = build_probe_diagnostics(
        window=probe_result,
        node_count=stats["node_count"],
        editable_node_count=stats["editable_node_count"],
        clickable_node_count=stats["clickable_node_count"],
        visible_node_count=stats["visible_node_count"],
    )
    diagnostics_report = build_diagnostics_report(
        window=probe_diagnostics["window"],
        node_stats=probe_diagnostics["node_stats"],
        input_candidates=ranked["candidates"],
        gate_result=gate_result,
        focus_result=focus_result,
        desktop_context=desktop_context,
        backend=backend,
    )
    bridge_result = build_windows_perception_result(
        probe_result=probe_result,
        desktop_context=desktop_context,
        focus_result=focus_result,
        diagnostics_report=diagnostics_report,
    )

    return {
        "ok": True,
        "probe_result": bridge_result["probe_result"],
        "diagnostics_report": bridge_result["diagnostics_report"],
        "desktop_context": bridge_result["desktop_context"],
        "focus_result": bridge_result["focus_result"],
    }


def main() -> None:
    if len(sys.argv) < 2:
        print_json(build_error_response("missing JSON argument"))
        return

    try:
        payload = json.loads(sys.argv[1])
    except json.JSONDecodeError as exc:
        print_json(build_error_response(f"invalid JSON: {exc.msg}"))
        return

    if not isinstance(payload, dict):
        print_json(build_error_response("request must be a JSON object"))
        return

    print_json(build_probe_payload(payload))


if __name__ == "__main__":
    configure_stdio()
    main()
