from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from codex_game_server.models import ServerManifest

MANIFEST_NAME = "server.json"


def manifest_path(path: Path) -> Path:
    candidate = path.expanduser()
    if candidate.is_dir() or candidate.suffix == "":
        return candidate / MANIFEST_NAME
    return candidate


def load_manifest(path: Path) -> ServerManifest:
    resolved = manifest_path(path)
    data = json.loads(resolved.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("manifest must be a JSON object")
    return ServerManifest.from_dict(data, source_path=resolved)


def save_manifest(manifest: ServerManifest) -> None:
    manifest.manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest.manifest_path.write_text(
        json.dumps(manifest.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def manifest_payload(path: Path) -> dict[str, Any]:
    return load_manifest(path).to_dict()
