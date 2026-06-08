from __future__ import annotations

import json
import os
import re
import shlex
import socket
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zipfile import ZIP_DEFLATED, ZipFile

from codex_game_server.game_support import SUPPORTED_GAMES, normalize_game, profile_for, profiles_payload, write_scaffold
from codex_game_server.manifest import MANIFEST_NAME, load_manifest, save_manifest
from codex_game_server.models import DEFAULT_CODEX_SETTINGS, DEFAULT_DIRECTORIES, ServerManifest

LOCAL_HOSTS = {"127.0.0.1", "localhost", "0.0.0.0", "::1"}


def init_server(
    root: Path,
    *,
    name: str | None = None,
    game: str = "generic",
    host: str = "127.0.0.1",
    port: int | None = None,
    start_command: list[str] | None = None,
    overwrite: bool = False,
) -> ServerManifest:
    server_root = root.expanduser()
    manifest_file = server_root / MANIFEST_NAME
    if manifest_file.exists() and not overwrite:
        raise ValueError(f"manifest already exists: {manifest_file}")

    try:
        profile = profile_for(game)
        normalized_game = profile.game
    except ValueError:
        normalized_game = normalize_game(game)
        profile = SUPPORTED_GAMES.get(normalized_game)
    directories = dict(profile.directories if profile else DEFAULT_DIRECTORIES)
    server_port = port if port is not None else (profile.default_port if profile else 25565)
    metadata = {}
    if profile:
        metadata["support_profile"] = profile.integration_kind

    manifest = ServerManifest(
        name=name or server_root.name or "game-server",
        game=normalized_game,
        host=host,
        port=server_port,
        start_command=list(start_command or []),
        directories=directories,
        codex=dict(DEFAULT_CODEX_SETTINGS),
        metadata=metadata,
        source_path=manifest_file,
    )
    manifest.validate()

    server_root.mkdir(parents=True, exist_ok=True)
    for directory in manifest.directory_paths().values():
        directory.mkdir(parents=True, exist_ok=True)
    save_manifest(manifest)
    return manifest


def supported_games() -> dict[str, Any]:
    return profiles_payload()


def scaffold_integration(
    path: Path,
    *,
    output: Path | None = None,
    game: str | None = None,
    overwrite: bool = False,
) -> dict[str, Any]:
    manifest = load_manifest(path)
    profile = profile_for(game or manifest.game)
    settings = manifest.codex_settings
    bridge_url = f"http://{settings['bridge_host']}:{settings['bridge_port']}"
    output_dir = output.expanduser() if output else manifest.root_path / "codex_integration"
    written = write_scaffold(profile, output_dir=output_dir, bridge_url=bridge_url, overwrite=overwrite)
    return {
        "game": profile.game,
        "integration_kind": profile.integration_kind,
        "maturity": profile.maturity,
        "output_dir": str(output_dir),
        "bridge_url": bridge_url,
        "commands": {
            "codex": settings["command_prefix"] + " *",
            "codex_func": settings["function_prefix"] + " *",
        },
        "files": written,
    }


def inspect_server(path: Path, *, include_health: bool = False) -> dict[str, Any]:
    manifest = load_manifest(path)
    directories = {
        key: _directory_info(directory)
        for key, directory in manifest.directory_paths().items()
    }
    plugins = list_plugins(path)
    backups = list_backups(path)
    payload: dict[str, Any] = {
        "manifest_path": str(manifest.manifest_path),
        "root_path": str(manifest.root_path),
        "name": manifest.name,
        "game": manifest.game,
        "host": manifest.host,
        "port": manifest.port,
        "start_command": list(manifest.start_command),
        "working_directory": str(manifest.working_path),
        "codex": manifest.codex_settings,
        "directories": directories,
        "plugin_count": len(plugins),
        "plugins": plugins,
        "backup_count": len(backups),
        "backups": backups,
        "port_availability": check_port_available(manifest.host, manifest.port),
    }
    if include_health:
        payload["health"] = check_health(path)
    return payload


def list_plugins(path: Path) -> list[dict[str, Any]]:
    manifest = load_manifest(path)
    plugin_dir = manifest.directory_path("plugins")
    if not plugin_dir.exists():
        return []

    plugins: list[dict[str, Any]] = []
    for item in sorted(plugin_dir.iterdir(), key=lambda candidate: candidate.name.lower()):
        kind = "directory" if item.is_dir() else "file"
        plugins.append(
            {
                "name": item.name,
                "path": str(item),
                "kind": kind,
                "size_bytes": _path_size(item),
                "modified_at": _modified_at(item),
            }
        )
    return plugins


def list_backups(path: Path) -> list[dict[str, Any]]:
    manifest = load_manifest(path)
    backup_dir = manifest.directory_path("backups")
    if not backup_dir.exists():
        return []

    backups: list[dict[str, Any]] = []
    for item in sorted(backup_dir.glob("*.zip"), key=lambda candidate: candidate.stat().st_mtime, reverse=True):
        backups.append(
            {
                "name": item.name,
                "path": str(item),
                "size_bytes": item.stat().st_size,
                "modified_at": _modified_at(item),
            }
        )
    return backups


def create_backup(path: Path, *, label: str = "manual") -> dict[str, Any]:
    manifest = load_manifest(path)
    world_dir = manifest.directory_path("world")
    if not world_dir.exists():
        raise ValueError(f"world directory does not exist: {world_dir}")

    backup_dir = manifest.directory_path("backups")
    backup_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    safe_name = _safe_token(manifest.name)
    safe_label = _safe_token(label)
    backup_path = backup_dir / f"{safe_name}-{timestamp}-{safe_label}.zip"

    file_count = 0
    with ZipFile(backup_path, "w", compression=ZIP_DEFLATED) as archive:
        for item in sorted(world_dir.rglob("*")):
            if not item.is_file():
                continue
            archive.write(item, Path("world") / item.relative_to(world_dir))
            file_count += 1
        archive.writestr(
            "_codex_game_server/server.json",
            json.dumps(manifest.to_dict(), indent=2, sort_keys=True) + "\n",
        )

    return {
        "path": str(backup_path),
        "label": safe_label,
        "file_count": file_count,
        "size_bytes": backup_path.stat().st_size,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def check_health(path: Path, *, timeout: float = 1.0) -> dict[str, Any]:
    manifest = load_manifest(path)
    try:
        with socket.create_connection((manifest.host, manifest.port), timeout=timeout):
            return {
                "host": manifest.host,
                "port": manifest.port,
                "status": "open",
                "error": None,
            }
    except OSError as exc:
        return {
            "host": manifest.host,
            "port": manifest.port,
            "status": "closed",
            "error": str(exc),
        }


def check_port_available(host: str, port: int) -> dict[str, Any]:
    if host not in LOCAL_HOSTS:
        return {
            "host": host,
            "port": port,
            "available": None,
            "reason": "availability checks are only attempted for local hosts",
        }

    bind_host = "127.0.0.1" if host == "localhost" else host
    family = socket.AF_INET6 if bind_host == "::1" else socket.AF_INET
    with socket.socket(family, socket.SOCK_STREAM) as sock:
        try:
            sock.bind((bind_host, port))
        except OSError as exc:
            return {"host": host, "port": port, "available": False, "reason": str(exc)}
    return {"host": host, "port": port, "available": True, "reason": None}


def run_server(path: Path, *, dry_run: bool = False) -> dict[str, Any]:
    manifest = load_manifest(path)
    if not manifest.start_command:
        raise ValueError("start_command is empty; edit server.json or re-run init with --start-command")

    command = list(manifest.start_command)
    cwd = manifest.working_path
    payload = {
        "cwd": str(cwd),
        "argv": command,
        "command": shlex.join(command),
    }
    if dry_run:
        return payload

    env = os.environ.copy()
    env.update(manifest.env)
    completed = subprocess.run(command, cwd=cwd, env=env, check=False)
    payload["return_code"] = completed.returncode
    return payload


def _directory_info(path: Path) -> dict[str, Any]:
    return {
        "path": str(path),
        "exists": path.exists(),
        "file_count": _file_count(path),
        "size_bytes": _path_size(path),
    }


def _file_count(path: Path) -> int:
    if not path.exists():
        return 0
    if path.is_file():
        return 1
    return sum(1 for item in path.rglob("*") if item.is_file())


def _path_size(path: Path) -> int:
    if not path.exists():
        return 0
    if path.is_file():
        return path.stat().st_size
    return sum(item.stat().st_size for item in path.rglob("*") if item.is_file())


def _modified_at(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()


def _safe_token(value: str) -> str:
    token = re.sub(r"[^A-Za-z0-9_.-]+", "-", value.strip()).strip("-")
    return token or "unnamed"
