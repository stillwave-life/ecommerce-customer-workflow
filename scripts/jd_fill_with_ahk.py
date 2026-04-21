from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any



def build_result(
    *,
    ok: bool,
    executed: bool,
    effective_ahk_path: str,
    effective_script_path: str,
    effective_text_length: int,
    command_args: list[str],
    log_path: str,
    diagnostics_path: str | None = None,
    screenshots: dict[str, str] | None = None,
    **extra: Any,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "ok": ok,
        "executed": executed,
        "fill_visually_confirmed": False,
        "requires_manual_confirmation": True,
        "auto_send_allowed": False,
        "send_policy": "manual_only",
        "requires_admin": True,
        "ahk_path": effective_ahk_path,
        "effective_ahk_path": effective_ahk_path,
        "effective_script_path": effective_script_path,
        "effective_text_length": effective_text_length,
        "command_args": command_args,
        "script_path": effective_script_path,
        "log_path": log_path,
        "diagnostics_path": diagnostics_path,
        "screenshots": screenshots or {},
    }
    result.update(extra)
    return result



def load_diagnostics() -> tuple[str | None, dict[str, str]]:
    diagnostics_path: str | None = None
    screenshots: dict[str, str] = {}

    if LOG_PATH.exists():
        try:
            for raw_line in LOG_PATH.read_text(encoding="utf-8").splitlines():
                if "|" not in raw_line:
                    continue
                message = raw_line.split("|", 1)[1].strip()
                if message.startswith("diagnostics_path="):
                    diagnostics_path = message.split("=", 1)[1].strip()
                elif message.startswith("before_full="):
                    screenshots["before_full"] = message.split("=", 1)[1].strip()
                elif message.startswith("after_full="):
                    screenshots["after_full"] = message.split("=", 1)[1].strip()
                elif message.startswith("after_input="):
                    screenshots["after_input"] = message.split("=", 1)[1].strip()
        except OSError:
            pass

    if diagnostics_path:
        run_json_path = Path(diagnostics_path) / "run.json"
        if run_json_path.exists():
            try:
                payload = json.loads(run_json_path.read_text(encoding="utf-8-sig"))
                payload_screenshots = payload.get("screenshots")
                if isinstance(payload_screenshots, dict):
                    screenshots = {
                        key: str(value)
                        for key, value in payload_screenshots.items()
                        if isinstance(value, str) and value.strip()
                    }
            except (OSError, json.JSONDecodeError):
                pass

    return diagnostics_path, screenshots


SCRIPT_PATH = Path(__file__).resolve().with_name("jd_force_paste_ahk.ahk")
DEFAULT_AHK_PATH = Path(r"C:\Program Files\AutoHotkey\v2\AutoHotkey64.exe")
LOG_PATH = SCRIPT_PATH.with_name("jd_force_paste_ahk.log")


def configure_stdio() -> None:
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            reconfigure(encoding="utf-8")


def print_json(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False))


def fill_with_ahk(text: str, ahk_path: str | None = None) -> dict[str, Any]:
    effective_ahk_path = str(Path(ahk_path)) if ahk_path else str(DEFAULT_AHK_PATH)
    effective_script_path = str(SCRIPT_PATH)
    effective_text_length = len(text)
    command_args = [effective_ahk_path, effective_script_path, text]
    log_path = str(LOG_PATH)
    executable = Path(effective_ahk_path)
    if not executable.exists():
        return build_result(
            ok=False,
            executed=False,
            effective_ahk_path=effective_ahk_path,
            effective_script_path=effective_script_path,
            effective_text_length=effective_text_length,
            command_args=command_args,
            log_path=log_path,
            reason="ahk_not_found",
        )

    if not SCRIPT_PATH.exists():
        return build_result(
            ok=False,
            executed=False,
            effective_ahk_path=effective_ahk_path,
            effective_script_path=effective_script_path,
            effective_text_length=effective_text_length,
            command_args=command_args,
            log_path=log_path,
            reason="ahk_script_not_found",
        )

    try:
        completed = subprocess.run(
            command_args,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            timeout=60,
        )
    except subprocess.TimeoutExpired as exc:
        diagnostics_path, screenshots = load_diagnostics()
        return build_result(
            ok=False,
            executed=True,
            effective_ahk_path=effective_ahk_path,
            effective_script_path=effective_script_path,
            effective_text_length=effective_text_length,
            command_args=command_args,
            log_path=log_path,
            diagnostics_path=diagnostics_path,
            screenshots=screenshots,
            reason="ahk_execution_timeout",
            message=str(exc),
        )
    except OSError as exc:
        diagnostics_path, screenshots = load_diagnostics()
        return build_result(
            ok=False,
            executed=False,
            effective_ahk_path=effective_ahk_path,
            effective_script_path=effective_script_path,
            effective_text_length=effective_text_length,
            command_args=command_args,
            log_path=log_path,
            diagnostics_path=diagnostics_path,
            screenshots=screenshots,
            reason="ahk_execution_failed",
            message=str(exc),
        )

    diagnostics_path, screenshots = load_diagnostics()
    if completed.returncode != 0:
        return build_result(
            ok=False,
            executed=True,
            effective_ahk_path=effective_ahk_path,
            effective_script_path=effective_script_path,
            effective_text_length=effective_text_length,
            command_args=command_args,
            log_path=log_path,
            diagnostics_path=diagnostics_path,
            screenshots=screenshots,
            reason="ahk_execution_failed",
            returncode=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )

    return build_result(
        ok=True,
        executed=True,
        effective_ahk_path=effective_ahk_path,
        effective_script_path=effective_script_path,
        effective_text_length=effective_text_length,
        command_args=command_args,
        log_path=log_path,
        diagnostics_path=diagnostics_path,
        screenshots=screenshots,
    )


def parse_request(argv: list[str], stdin_text: str | None = None) -> tuple[str, str | None, dict[str, Any] | None]:
    if not argv:
        raise ValueError("missing_argument")

    ahk_path: str | None = None
    parsed_payload: dict[str, Any] | None = None
    input_mode = "arg"

    if argv[0] == "--file":
        if len(argv) < 2:
            raise ValueError("missing_file_path")
        payload_path = Path(argv[1])
        if not payload_path.exists():
            raise FileNotFoundError("payload_file_not_found")
        try:
            raw_input = payload_path.read_text(encoding="utf-8-sig")
        except OSError as exc:
            raise OSError("payload_file_read_failed") from exc
        input_mode = "file"
    elif argv[0] == "--stdin":
        raw_input = stdin_text if stdin_text is not None else sys.stdin.read()
        input_mode = "stdin"
    else:
        raw_input = argv[0]

    try:
        candidate = json.loads(raw_input)
    except json.JSONDecodeError:
        escaped_raw_input = raw_input.replace("\\", "\\\\")
        try:
            candidate = json.loads(escaped_raw_input)
        except json.JSONDecodeError:
            if input_mode in {"file", "stdin"}:
                raise ValueError("invalid_json")
            return raw_input, ahk_path, None

    if isinstance(candidate, dict):
        parsed_payload = candidate
        text = str(candidate.get("text", "测试填充123"))
        ahk_value = candidate.get("ahk_path")
        ahk_path = str(ahk_value) if ahk_value else None
        return text, ahk_path, parsed_payload

    if input_mode in {"file", "stdin"}:
        raise ValueError("invalid_json")
    return raw_input, ahk_path, None


def main() -> None:
    try:
        text, ahk_path, _ = parse_request(sys.argv[1:])
    except ValueError as exc:
        print_json({"ok": False, "executed": False, "reason": str(exc)})
        return
    except FileNotFoundError as exc:
        print_json({"ok": False, "executed": False, "reason": str(exc)})
        return
    except OSError as exc:
        print_json({"ok": False, "executed": False, "reason": str(exc)})
        return

    print_json(fill_with_ahk(text=text, ahk_path=ahk_path))


if __name__ == "__main__":
    configure_stdio()
    main()
