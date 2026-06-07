from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from codex_game_server.accounts import is_admin, list_admins
from codex_game_server.codex_runtime import check_codex_login, invoke_codex
from codex_game_server.manifest import load_manifest
from codex_game_server.operations import check_health, create_backup, inspect_server, list_plugins


def serve_bridge(
    path: Path,
    *,
    host: str | None = None,
    port: int | None = None,
    require_codex_login: bool = True,
    dry_run: bool = False,
) -> None:
    manifest = load_manifest(path)
    codex_settings = manifest.codex_settings
    bind_host = host or str(codex_settings.get("bridge_host", "127.0.0.1"))
    bind_port = int(port or codex_settings.get("bridge_port", 8766))

    if require_codex_login:
        status = check_codex_login()
        if not status["available"] or not status["authenticated"]:
            raise RuntimeError(f"codex login is not ready: {status.get('error')}")

    handler = _handler_factory(path, dry_run=dry_run)
    server = ThreadingHTTPServer((bind_host, bind_port), handler)
    server.serve_forever()


def codex_request(path: Path, *, account: str, prompt: str, dry_run: bool = False) -> dict[str, Any]:
    manifest = load_manifest(path)
    if not is_admin(path, account=account, game=manifest.game):
        return {
            "ok": False,
            "status": "unauthorized",
            "message": f"account is not registered as a Codex admin: {account}",
        }
    if not prompt.strip():
        return {"ok": False, "status": "bad_request", "message": "prompt is required"}

    if dry_run:
        return {
            "ok": True,
            "status": "dry_run",
            "message": f"Codex prompt accepted for {account}: {prompt}",
        }

    status = check_codex_login()
    if not status["available"] or not status["authenticated"]:
        return {"ok": False, "status": "codex_unavailable", "message": status.get("error")}

    result = invoke_codex(prompt, cwd=manifest.root_path)
    return {
        "ok": result["return_code"] == 0,
        "status": "completed" if result["return_code"] == 0 else "failed",
        "message": result["stdout"] or result["stderr"],
        "codex": result,
    }


def codex_func_request(path: Path, *, account: str, command: str) -> dict[str, Any]:
    manifest = load_manifest(path)
    if not is_admin(path, account=account, game=manifest.game):
        return {
            "ok": False,
            "status": "unauthorized",
            "message": f"account is not registered as a Codex admin: {account}",
        }

    parts = command.strip().split()
    verb = parts[0].lower() if parts else "help"
    args = parts[1:]
    if verb == "help":
        message = "available functions: help, status, admins, plugins, backup <label>"
        return {"ok": True, "status": "ok", "message": message}
    if verb == "status":
        return {"ok": True, "status": "ok", "message": "server status collected", "data": inspect_server(path)}
    if verb == "admins":
        return {"ok": True, "status": "ok", "message": "admin accounts listed", "data": list_admins(path)}
    if verb == "plugins":
        return {"ok": True, "status": "ok", "message": "plugins listed", "data": list_plugins(path)}
    if verb == "health":
        return {"ok": True, "status": "ok", "message": "health checked", "data": check_health(path)}
    if verb == "backup":
        label = "-".join(args) if args else "ingame"
        return {"ok": True, "status": "ok", "message": "backup created", "data": create_backup(path, label=label)}
    return {"ok": False, "status": "unknown_function", "message": f"unknown function: {verb}"}


def _handler_factory(path: Path, *, dry_run: bool) -> type[BaseHTTPRequestHandler]:
    class BridgeHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            if self.path != "/health":
                self._write_json({"ok": False, "message": "not found"}, status=HTTPStatus.NOT_FOUND)
                return
            self._write_json({"ok": True, "codex": check_codex_login(), "server": load_manifest(path).to_dict()})

        def do_POST(self) -> None:
            payload = self._read_json()
            account = str(payload.get("account", ""))
            if self.path == "/v1/codex":
                result = codex_request(path, account=account, prompt=str(payload.get("prompt", "")), dry_run=dry_run)
                self._write_json(result, status=_http_status(result))
                return
            if self.path == "/v1/codex_func":
                result = codex_func_request(path, account=account, command=str(payload.get("command", "")))
                self._write_json(result, status=_http_status(result))
                return
            self._write_json({"ok": False, "message": "not found"}, status=HTTPStatus.NOT_FOUND)

        def log_message(self, format: str, *args: Any) -> None:
            return

        def _read_json(self) -> dict[str, Any]:
            length = int(self.headers.get("Content-Length", "0") or "0")
            raw = self.rfile.read(length) if length else b"{}"
            try:
                payload = json.loads(raw.decode("utf-8"))
            except json.JSONDecodeError:
                return {}
            return payload if isinstance(payload, dict) else {}

        def _write_json(self, payload: dict[str, Any], *, status: HTTPStatus = HTTPStatus.OK) -> None:
            body = json.dumps(payload, sort_keys=True).encode("utf-8")
            self.send_response(status.value)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    return BridgeHandler


def _http_status(result: dict[str, Any]) -> HTTPStatus:
    if result.get("ok"):
        return HTTPStatus.OK
    if result.get("status") == "unauthorized":
        return HTTPStatus.FORBIDDEN
    if result.get("status") == "bad_request":
        return HTTPStatus.BAD_REQUEST
    return HTTPStatus.BAD_GATEWAY
