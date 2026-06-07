from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any


def check_codex_login(
    *,
    codex_bin: str = "codex",
    include_doctor: bool = False,
    timeout: float = 20.0,
) -> dict[str, Any]:
    executable = shutil.which(codex_bin)
    if executable is None:
        return {
            "available": False,
            "authenticated": False,
            "codex_bin": codex_bin,
            "executable": None,
            "version": None,
            "login_status": None,
            "doctor": None,
            "error": "codex executable was not found on PATH",
        }

    version = _run_command([executable, "--version"], timeout=timeout)
    login = _run_command([executable, "login", "status"], timeout=timeout)
    authenticated = login["return_code"] == 0
    doctor = _doctor_report(executable, timeout=timeout) if include_doctor else None

    return {
        "available": True,
        "authenticated": authenticated,
        "codex_bin": codex_bin,
        "executable": executable,
        "version": _first_line(version["stdout"]) or None,
        "login_status": login,
        "doctor": doctor,
        "error": None if authenticated else _first_line(login["stderr"]) or _first_line(login["stdout"]),
    }


def invoke_codex(
    prompt: str,
    *,
    cwd: Path,
    codex_bin: str = "codex",
    timeout: float = 120.0,
    model: str | None = None,
    sandbox: str = "read-only",
) -> dict[str, Any]:
    executable = shutil.which(codex_bin)
    if executable is None:
        raise RuntimeError("codex executable was not found on PATH")

    command = [
        executable,
        "exec",
        "--skip-git-repo-check",
        "--ephemeral",
        "--sandbox",
        sandbox,
        "-C",
        str(cwd),
    ]
    if model:
        command.extend(["--model", model])
    command.append(prompt)

    result = _run_command(command, timeout=timeout)
    result["command"] = _redacted_command(command)
    return result


def _doctor_report(executable: str, *, timeout: float) -> dict[str, Any] | None:
    result = _run_command([executable, "doctor", "--json"], timeout=timeout)
    try:
        payload = json.loads(result["stdout"])
    except json.JSONDecodeError:
        payload = None
    return {
        "return_code": result["return_code"],
        "payload": payload,
        "stdout": result["stdout"] if payload is None else "",
        "stderr": result["stderr"],
    }


def _run_command(command: list[str], *, timeout: float) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            command,
            text=True,
            capture_output=True,
            check=False,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "return_code": None,
            "stdout": exc.stdout or "",
            "stderr": exc.stderr or "",
            "timed_out": True,
        }

    return {
        "return_code": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
        "timed_out": False,
    }


def _first_line(value: str | None) -> str:
    if not value:
        return ""
    return value.splitlines()[0].strip()


def _redacted_command(command: list[str]) -> list[str]:
    return [item if len(item) <= 120 else item[:117] + "..." for item in command]
