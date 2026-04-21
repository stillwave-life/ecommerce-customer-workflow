from __future__ import annotations

import ctypes
import json
import subprocess
from ctypes import wintypes
from importlib.util import find_spec
from pathlib import Path
from tempfile import gettempdir
from time import time
from typing import Any, Callable

from app.desktop.windows_adapter.jd_workspace_profile import get_jd_workspace_profile

DesktopFactory = Callable[[], Any]

JD_TITLE_KEYWORDS = ("咚咚", "融合工作台", "evw10158991")


class RECT(ctypes.Structure):
    _fields_ = [
        ("left", ctypes.c_long),
        ("top", ctypes.c_long),
        ("right", ctypes.c_long),
        ("bottom", ctypes.c_long),
    ]


def _user32() -> Any | None:
    windll = getattr(ctypes, "windll", None)
    if windll is None:
        return None
    return getattr(windll, "user32", None)


WINDOW_ENUM_PROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)


def _default_desktop_factory() -> Any:
    if find_spec("pywinauto") is None:
        raise ImportError("pywinauto fill backend is not available")
    from pywinauto import Desktop

    return Desktop(backend="uia")


def _readback_text(control: Any) -> str:
    for attr in ("window_text", "texts"):
        value = getattr(control, attr, None)
        if callable(value):
            result = value()
            if isinstance(result, list):
                joined = " ".join(str(item) for item in result if str(item).strip())
                if joined:
                    return joined
            elif result:
                return str(result)
    return str(getattr(control, "value", "") or "")


def _window_title(window: Any) -> str:
    for attr in ("window_text", "texts"):
        value = getattr(window, attr, None)
        if callable(value):
            result = value()
            if isinstance(result, list):
                joined = " ".join(str(item) for item in result if str(item).strip())
                if joined:
                    return joined
            elif result:
                return str(result)
    return ""


def _window_rect(window: Any) -> tuple[int, int, int, int]:
    rect = window.rectangle()
    left = int(getattr(rect, "left", 0))
    top = int(getattr(rect, "top", 0))
    right = int(getattr(rect, "right", left))
    bottom = int(getattr(rect, "bottom", top))
    return left, top, right, bottom


def _rect_is_reasonable(window_rect: tuple[int, int, int, int]) -> bool:
    left, top, right, bottom = window_rect
    return right > left and bottom > top and right - left >= 800 and bottom - top >= 500


def _resolve_region(bounds: list[Any], window_rect: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    left, top, right, bottom = window_rect
    width = max(right - left, 1)
    height = max(bottom - top, 1)
    if len(bounds) != 4:
        raise RuntimeError("fill_target_not_resolved")
    if all(isinstance(value, (int, float)) and 0 <= float(value) <= 1 for value in bounds):
        x1 = left + int(width * float(bounds[0]))
        y1 = top + int(height * float(bounds[1]))
        x2 = left + int(width * float(bounds[2]))
        y2 = top + int(height * float(bounds[3]))
    else:
        x1, y1, x2, y2 = tuple(int(value) for value in bounds)
    if x2 <= x1 or y2 <= y1:
        raise RuntimeError("fill_target_not_resolved")
    return x1, y1, x2, y2


def _capture_region(region: tuple[int, int, int, int], output_path: Path) -> bool:
    try:
        from PIL import ImageGrab
    except Exception:
        return False
    image = ImageGrab.grab(bbox=region)
    image.save(output_path)
    return True


def _compute_diff_score(before_path: Path, after_path: Path) -> float | None:
    try:
        from PIL import Image, ImageChops, ImageStat
    except Exception:
        return None
    before = Image.open(before_path).convert("L")
    after = Image.open(after_path).convert("L")
    diff = ImageChops.difference(before, after)
    stat = ImageStat.Stat(diff)
    mean_value = float(stat.mean[0]) if stat.mean else 0.0
    return mean_value / 255.0


def _create_diagnostics_dir() -> Path:
    diagnostics_dir = Path(gettempdir()) / "jd_fill_diagnostics" / f"fill_run_{int(time() * 1000)}"
    diagnostics_dir.mkdir(parents=True, exist_ok=True)
    return diagnostics_dir


def _write_run_json(diagnostics_dir: Path, payload: dict[str, Any]) -> None:
    (diagnostics_dir / "run.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _get_clipboard_text() -> tuple[bool, str]:
    try:
        import pyperclip

        return True, str(pyperclip.paste())
    except Exception:
        pass
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", "Get-Clipboard -Raw"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        return result.returncode == 0, result.stdout if result.returncode == 0 else ""
    except Exception:
        return False, ""


def _set_clipboard_text(text: str) -> bool:
    try:
        import pyperclip

        pyperclip.copy(text)
        return True
    except Exception:
        pass
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", "Set-Clipboard -Value $input"],
            input=text,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        return result.returncode == 0
    except Exception:
        return False


def _default_target_bounds(action: dict[str, Any]) -> list[Any]:
    bounds = action.get("target_bounds")
    if isinstance(bounds, list) and bounds:
        return bounds
    profile = get_jd_workspace_profile(str(action.get("ui_profile", "jd_maximized_default")))
    return list(profile["input_region"])


def _get_foreground_hwnd() -> int:
    user32 = _user32()
    if user32 is None:
        return 0
    try:
        return int(user32.GetForegroundWindow() or 0)
    except Exception:
        return 0


def _enumerate_top_windows() -> list[dict[str, Any]]:
    user32 = _user32()
    if user32 is None:
        return []

    candidates: list[dict[str, Any]] = []

    def _callback(hwnd: int, _lparam: int) -> bool:
        try:
            if not user32.IsWindowVisible(hwnd):
                return True
            title_buffer = ctypes.create_unicode_buffer(512)
            user32.GetWindowTextW(hwnd, title_buffer, 512)
            rect = RECT()
            if not user32.GetWindowRect(hwnd, ctypes.byref(rect)):
                return True
            candidates.append(
                {
                    "hwnd": int(hwnd),
                    "title": title_buffer.value or "",
                    "rect": (int(rect.left), int(rect.top), int(rect.right), int(rect.bottom)),
                    "visible": True,
                    "iconic": bool(user32.IsIconic(hwnd)),
                }
            )
        except Exception:
            return True
        return True

    user32.EnumWindows(WINDOW_ENUM_PROC(_callback), 0)
    return candidates


def _candidate_area(candidate: dict[str, Any]) -> int:
    left, top, right, bottom = candidate["rect"]
    return max(right - left, 0) * max(bottom - top, 0)


def _normalize_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    rect = tuple(int(value) for value in candidate.get("rect", (0, 0, 0, 0)))
    return {
        "hwnd": int(candidate.get("hwnd", 0)),
        "title": str(candidate.get("title", "")),
        "rect": rect,
        "visible": bool(candidate.get("visible", True)),
        "iconic": bool(candidate.get("iconic", False)),
    }


def _match_jd_window(candidates: list[dict[str, Any]], foreground_hwnd: int, title_hint: str = "") -> tuple[dict[str, Any] | None, list[str]]:
    warnings: list[str] = []
    normalized = [_normalize_candidate(candidate) for candidate in candidates]
    eligible = [candidate for candidate in normalized if candidate["visible"] and not candidate["iconic"] and _rect_is_reasonable(candidate["rect"])]
    if not eligible:
        return None, warnings

    foreground = next((candidate for candidate in eligible if candidate["hwnd"] == foreground_hwnd), None)
    foreground_title_matches = foreground is not None and (
        any(keyword in foreground["title"] for keyword in JD_TITLE_KEYWORDS) or (title_hint and title_hint in foreground["title"])
    )
    if foreground is not None and foreground_title_matches:
        matched = dict(foreground)
        matched["matched_by"] = "foreground"
        return matched, warnings

    title_filtered = [
        candidate
        for candidate in eligible
        if any(keyword in candidate["title"] for keyword in JD_TITLE_KEYWORDS) or (title_hint and title_hint in candidate["title"])
    ]
    if title_filtered:
        if foreground is not None:
            warnings.append("foreground_title_not_matched")
        matched = dict(sorted(title_filtered, key=_candidate_area, reverse=True)[0])
        matched["matched_by"] = "title_keyword"
        return matched, warnings

    if foreground is not None:
        matched = dict(foreground)
        matched["matched_by"] = "foreground"
        warnings.append("foreground_title_not_matched")
        return matched, warnings

    matched = dict(sorted(eligible, key=_candidate_area, reverse=True)[0])
    matched["matched_by"] = "fallback_rect"
    warnings.append("title_keyword_not_matched_using_largest_rect")
    return matched, warnings


def _resolve_target_window(desktop: Any, action: dict[str, Any], diagnostics_dir: Path | None = None) -> dict[str, Any]:
    diagnostics_dir = diagnostics_dir or _create_diagnostics_dir()
    foreground_hwnd = _get_foreground_hwnd()
    candidates = _enumerate_top_windows()
    matched_window, warnings = _match_jd_window(candidates, foreground_hwnd, str(action.get("window_title_hint", "")).strip())

    payload = {
        "stage": "window_resolution",
        "foreground_hwnd": foreground_hwnd,
        "candidate_windows": [
            {
                "hwnd": int(candidate.get("hwnd", 0)),
                "title": str(candidate.get("title", "")),
                "rect": list(candidate.get("rect", (0, 0, 0, 0))),
                "visible": bool(candidate.get("visible", True)),
                "iconic": bool(candidate.get("iconic", False)),
            }
            for candidate in candidates
        ],
        "matched_window": None,
        "reason": "",
        "warnings": warnings,
    }

    if matched_window is None:
        payload["reason"] = "jd_window_not_found"
        _write_run_json(diagnostics_dir, payload)
        return {
            "ok": False,
            "stage": "window_resolution",
            "foreground_hwnd": foreground_hwnd,
            "candidate_windows": payload["candidate_windows"],
            "matched_window": None,
            "reason": "jd_window_not_found",
            "warnings": warnings,
            "diagnostics_path": str(diagnostics_dir),
        }

    payload["matched_window"] = {
        "hwnd": matched_window["hwnd"],
        "title": matched_window["title"],
        "rect": list(matched_window["rect"]),
        "matched_by": matched_window["matched_by"],
    }
    payload["reason"] = ""
    _write_run_json(diagnostics_dir, payload)

    try:
        window = desktop.window(handle=matched_window["hwnd"])
    except Exception as exc:
        payload["reason"] = str(exc) or "window_wrapper_resolution_failed"
        _write_run_json(diagnostics_dir, payload)
        return {
            "ok": False,
            "stage": "window_resolution",
            "foreground_hwnd": foreground_hwnd,
            "candidate_windows": payload["candidate_windows"],
            "matched_window": payload["matched_window"],
            "reason": payload["reason"],
            "warnings": warnings,
            "diagnostics_path": str(diagnostics_dir),
        }

    return {
        "ok": True,
        "stage": "window_resolution",
        "foreground_hwnd": foreground_hwnd,
        "candidate_windows": payload["candidate_windows"],
        "matched_window": payload["matched_window"],
        "reason": "",
        "warnings": warnings,
        "diagnostics_path": str(diagnostics_dir),
        "window": window,
    }


def _fill_text_by_coordinates(action: dict[str, Any], desktop: Any) -> dict[str, Any]:
    diagnostics_dir = _create_diagnostics_dir()
    warnings: list[str] = []
    reason = ""
    error = ""
    stage = "window_resolution"
    window_title = ""
    window_rect = (0, 0, 0, 0)
    region = (0, 0, 0, 0)
    click_point = (0, 0)
    diff_score: float | None = None
    diff_passed = False
    clipboard_backup_ok = False
    clipboard_restore_ok = False
    text = str(action.get("text", ""))

    run_payload: dict[str, Any] = {
        "stage": stage,
        "foreground_hwnd": 0,
        "candidate_windows": [],
        "matched_window": None,
        "window_title": window_title,
        "window_rect": list(window_rect),
        "target_region": list(region),
        "click_point": list(click_point),
        "text_length": len(text),
        "verification_method": "screenshot_diff",
        "diff_score": diff_score,
        "diff_passed": diff_passed,
        "clipboard_backup_ok": clipboard_backup_ok,
        "clipboard_restore_ok": clipboard_restore_ok,
        "warning": warnings,
        "error": error,
        "reason": reason,
    }

    try:
        resolved = _resolve_target_window(desktop, action, diagnostics_dir=diagnostics_dir)
        run_payload["foreground_hwnd"] = resolved.get("foreground_hwnd", 0)
        run_payload["candidate_windows"] = resolved.get("candidate_windows", [])
        run_payload["matched_window"] = resolved.get("matched_window")
        warnings.extend(resolved.get("warnings", []))
        if not resolved.get("ok"):
            reason = str(resolved.get("reason", "jd_window_not_found"))
            raise RuntimeError(reason)

        window = resolved["window"]
        matched_window = resolved["matched_window"] or {}
        window_title = str(matched_window.get("title", ""))
        window_rect = tuple(matched_window.get("rect", (0, 0, 0, 0)))
        region = _resolve_region(_default_target_bounds(action), window_rect)
        region_width = region[2] - region[0]
        region_height = region[3] - region[1]
        click_point = (region[0] + int(region_width * 0.35), region[1] + int(region_height * 0.45))

        stage = "click_input"
        before_path = diagnostics_dir / "before_input.png"
        after_path = diagnostics_dir / "after_input.png"
        before_captured = _capture_region(region, before_path)
        if not before_captured:
            warnings.append("before_screenshot_failed")
        window.click_input(coords=(click_point[0] - window_rect[0], click_point[1] - window_rect[1]))

        stage = "clipboard_set"
        clipboard_backup_ok, clipboard_backup = _get_clipboard_text()
        if not clipboard_backup_ok:
            warnings.append("clipboard_backup_failed")
        clipboard_set_ok = _set_clipboard_text(text) if action.get("paste_via_clipboard", True) else False
        if action.get("paste_via_clipboard", True) and not clipboard_set_ok:
            warnings.append("clipboard_set_failed_using_type_keys")

        stage = "paste"
        if action.get("clear_before_fill"):
            window.type_keys("^a")
        if action.get("paste_via_clipboard", True) and clipboard_set_ok:
            window.type_keys("^v")
        else:
            window.type_keys(text, with_spaces=True, set_foreground=False)

        stage = "screenshot_diff"
        after_captured = _capture_region(region, after_path)
        if not after_captured:
            warnings.append("after_screenshot_failed")
        if before_captured and after_captured:
            diff_score = _compute_diff_score(before_path, after_path)
        diff_passed = diff_score is not None and diff_score >= 0.01
        if not diff_passed:
            reason = "screenshot_diff_failed"

        if clipboard_backup_ok:
            clipboard_restore_ok = _set_clipboard_text(clipboard_backup)
            if not clipboard_restore_ok:
                warnings.append("clipboard_restore_failed")
    except Exception as exc:
        error = type(exc).__name__
        if not reason:
            reason = str(exc) or stage
    finally:
        run_payload.update(
            {
                "stage": stage,
                "window_title": window_title,
                "window_rect": list(window_rect),
                "target_region": list(region),
                "click_point": list(click_point),
                "text_length": len(text),
                "verification_method": "screenshot_diff",
                "diff_score": diff_score,
                "diff_passed": diff_passed,
                "clipboard_backup_ok": clipboard_backup_ok,
                "clipboard_restore_ok": clipboard_restore_ok,
                "warning": warnings,
                "error": error,
                "reason": reason,
            }
        )
        _write_run_json(diagnostics_dir, run_payload)

    if error and reason != "screenshot_diff_failed":
        raise RuntimeError(reason)

    return {
        "target_name": window_title or "reply_box",
        "written_text": text,
        "verification_method": "screenshot_diff",
        "diff_score": diff_score,
        "diff_passed": diff_passed,
        "diagnostics_path": str(diagnostics_dir),
        "reason": reason,
        "stage": stage,
    }


def click_coordinates_action(action: dict[str, Any], desktop_factory: DesktopFactory | None = None) -> dict[str, Any]:
    desktop_factory = desktop_factory or _default_desktop_factory
    desktop = desktop_factory()
    diagnostics_dir = _create_diagnostics_dir()
    resolved = _resolve_target_window(desktop, action, diagnostics_dir=diagnostics_dir)
    if not resolved.get("ok"):
        return resolved

    matched_window = resolved["matched_window"] or {}
    window = resolved["window"]
    window_title = str(matched_window.get("title", ""))
    window_rect = tuple(matched_window.get("rect", (0, 0, 0, 0)))
    region = _resolve_region(_default_target_bounds(action), window_rect)
    click_point = (region[0] + (region[2] - region[0]) // 2, region[1] + (region[3] - region[1]) // 2)
    before_path = diagnostics_dir / "before_input.png"
    after_path = diagnostics_dir / "after_input.png"
    _capture_region(region, before_path)
    window.click_input(coords=(click_point[0] - window_rect[0], click_point[1] - window_rect[1]))
    _capture_region(region, after_path)
    payload = {
        "stage": "click_input",
        "foreground_hwnd": resolved.get("foreground_hwnd", 0),
        "candidate_windows": resolved.get("candidate_windows", []),
        "matched_window": matched_window,
        "window_title": window_title,
        "window_rect": list(window_rect),
        "target_region": list(region),
        "click_point": list(click_point),
        "text_length": 0,
        "verification_method": "before_after_screenshot",
        "diff_score": _compute_diff_score(before_path, after_path),
        "diff_passed": None,
        "clipboard_backup_ok": False,
        "clipboard_restore_ok": False,
        "warning": resolved.get("warnings", []),
        "error": "",
        "reason": "",
    }
    _write_run_json(diagnostics_dir, payload)
    return {"ok": True, "action_name": action.get("name"), "diagnostics_path": str(diagnostics_dir), **payload}


def fill_text(action: dict[str, Any], desktop_factory: DesktopFactory | None = None) -> dict[str, Any]:
    desktop_factory = desktop_factory or _default_desktop_factory
    desktop = desktop_factory()

    target_automation_id = str(action.get("target_automation_id", "")).strip()
    target_name = str(action.get("target_name", "")).strip()
    text = str(action.get("text", ""))
    targeting_strategy = str(action.get("targeting_strategy", "")).strip()

    if targeting_strategy == "coordinates" or (not target_automation_id and not target_name):
        return _fill_text_by_coordinates(action, desktop)

    if target_automation_id:
        control = desktop.window(auto_id=target_automation_id)
    elif target_name:
        control = desktop.window(title=target_name)
    else:
        raise RuntimeError("fill_target_not_resolved")

    setter = getattr(control, "set_edit_text", None)
    if not callable(setter):
        raise RuntimeError("fill_target_not_editable")

    setter(text)
    return {
        "target_name": target_name,
        "written_text": _readback_text(control),
        "verification_method": "readback",
    }
