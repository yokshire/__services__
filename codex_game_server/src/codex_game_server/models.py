from __future__ import annotations

import shlex
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

DEFAULT_DIRECTORIES: dict[str, str] = {
    "world": "world",
    "plugins": "plugins",
    "backups": "backups",
    "logs": "logs",
}

DEFAULT_CODEX_SETTINGS: dict[str, Any] = {
    "bridge_host": "127.0.0.1",
    "bridge_port": 8766,
    "command_prefix": "/codex",
    "function_prefix": "/codex_func",
    "require_admin": True,
}

REQUIRED_DIRECTORY_KEYS = frozenset(DEFAULT_DIRECTORIES)


@dataclass
class ServerManifest:
    name: str
    game: str
    host: str
    port: int
    start_command: list[str] = field(default_factory=list)
    working_directory: str = "."
    directories: dict[str, str] = field(default_factory=lambda: dict(DEFAULT_DIRECTORIES))
    codex: dict[str, Any] = field(default_factory=lambda: dict(DEFAULT_CODEX_SETTINGS))
    env: dict[str, str] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    schema_version: int = 1
    source_path: Path | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any], *, source_path: Path | None = None) -> "ServerManifest":
        start_command = data.get("start_command", [])
        if isinstance(start_command, str):
            start_command = shlex.split(start_command)
        if not isinstance(start_command, list) or not all(isinstance(item, str) for item in start_command):
            raise ValueError("start_command must be a string or list of strings")

        directories = dict(DEFAULT_DIRECTORIES)
        incoming_directories = data.get("directories", {})
        if not isinstance(incoming_directories, dict):
            raise ValueError("directories must be an object")
        for key, value in incoming_directories.items():
            if not isinstance(key, str) or not isinstance(value, str) or not value:
                raise ValueError("directories entries must be non-empty string paths")
            directories[key] = value

        env = data.get("env", {})
        if not isinstance(env, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in env.items()):
            raise ValueError("env must be an object of string values")

        codex = dict(DEFAULT_CODEX_SETTINGS)
        incoming_codex = data.get("codex", {})
        if not isinstance(incoming_codex, dict):
            raise ValueError("codex must be an object")
        codex.update(incoming_codex)

        tags = data.get("tags", [])
        if not isinstance(tags, list) or not all(isinstance(item, str) for item in tags):
            raise ValueError("tags must be a list of strings")

        metadata = data.get("metadata", {})
        if not isinstance(metadata, dict):
            raise ValueError("metadata must be an object")

        manifest = cls(
            schema_version=int(data.get("schema_version", 1)),
            name=_required_string(data, "name"),
            game=_required_string(data, "game"),
            host=str(data.get("host", "127.0.0.1")),
            port=int(data.get("port", 25565)),
            start_command=list(start_command),
            working_directory=str(data.get("working_directory", ".")),
            directories=directories,
            codex=codex,
            env=dict(env),
            tags=list(tags),
            metadata=dict(metadata),
            source_path=source_path,
        )
        manifest.validate()
        return manifest

    @property
    def root_path(self) -> Path:
        if self.source_path is None:
            return Path.cwd()
        return self.source_path.parent

    @property
    def manifest_path(self) -> Path:
        if self.source_path is None:
            return self.root_path / "server.json"
        return self.source_path

    @property
    def working_path(self) -> Path:
        return self.resolve_path(self.working_directory)

    @property
    def codex_settings(self) -> dict[str, Any]:
        return dict(self.codex)

    def directory_path(self, key: str) -> Path:
        try:
            value = self.directories[key]
        except KeyError as exc:
            raise ValueError(f"unknown directory key: {key}") from exc
        return self.resolve_path(value)

    def directory_paths(self) -> dict[str, Path]:
        return {key: self.directory_path(key) for key in sorted(self.directories)}

    def resolve_path(self, value: str) -> Path:
        path = Path(value).expanduser()
        if path.is_absolute():
            return path
        return self.root_path / path

    def validate(self) -> None:
        if self.schema_version != 1:
            raise ValueError(f"unsupported schema_version: {self.schema_version}")
        if not self.name.strip():
            raise ValueError("name is required")
        if not self.game.strip():
            raise ValueError("game is required")
        if not self.host.strip():
            raise ValueError("host is required")
        if not 1 <= self.port <= 65535:
            raise ValueError("port must be between 1 and 65535")
        bridge_port = int(self.codex.get("bridge_port", 8766))
        if not 1 <= bridge_port <= 65535:
            raise ValueError("codex.bridge_port must be between 1 and 65535")
        if not str(self.codex.get("command_prefix", "")).startswith("/"):
            raise ValueError("codex.command_prefix must start with /")
        if not str(self.codex.get("function_prefix", "")).startswith("/"):
            raise ValueError("codex.function_prefix must start with /")
        missing = REQUIRED_DIRECTORY_KEYS - set(self.directories)
        if missing:
            raise ValueError(f"missing required directories: {', '.join(sorted(missing))}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "name": self.name,
            "game": self.game,
            "host": self.host,
            "port": self.port,
            "start_command": list(self.start_command),
            "working_directory": self.working_directory,
            "directories": dict(sorted(self.directories.items())),
            "codex": dict(sorted(self.codex.items())),
            "env": dict(sorted(self.env.items())),
            "tags": list(self.tags),
            "metadata": dict(self.metadata),
        }


def _required_string(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} is required")
    return value
