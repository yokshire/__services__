from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from codex_game_server.manifest import load_manifest

ADMIN_REGISTRY_NAME = "codex_admins.json"


@dataclass
class AdminAccount:
    account: str
    game: str
    display_name: str
    roles: list[str] = field(default_factory=lambda: ["admin"])
    active: bool = True
    added_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AdminAccount":
        roles = data.get("roles", ["admin"])
        if not isinstance(roles, list) or not all(isinstance(role, str) for role in roles):
            raise ValueError("admin roles must be a list of strings")
        metadata = data.get("metadata", {})
        if not isinstance(metadata, dict):
            raise ValueError("admin metadata must be an object")
        return cls(
            account=_required_string(data, "account"),
            game=_required_string(data, "game"),
            display_name=str(data.get("display_name") or data["account"]),
            roles=roles,
            active=bool(data.get("active", True)),
            added_at=str(data.get("added_at") or datetime.now(timezone.utc).isoformat()),
            metadata=dict(metadata),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "account": self.account,
            "game": self.game,
            "display_name": self.display_name,
            "roles": list(self.roles),
            "active": self.active,
            "added_at": self.added_at,
            "metadata": dict(self.metadata),
        }


def registry_path(path: Path) -> Path:
    manifest = load_manifest(path)
    return manifest.root_path / ADMIN_REGISTRY_NAME


def load_admins(path: Path) -> dict[str, Any]:
    file_path = registry_path(path)
    if not file_path.exists():
        return {"schema_version": 1, "accounts": {}}

    payload = json.loads(file_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("admin registry must be a JSON object")
    accounts = payload.get("accounts", {})
    if not isinstance(accounts, dict):
        raise ValueError("admin registry accounts must be an object")

    normalized: dict[str, dict[str, Any]] = {}
    for key, value in accounts.items():
        if not isinstance(value, dict):
            raise ValueError(f"admin account entry must be an object: {key}")
        account = AdminAccount.from_dict(value)
        normalized[_account_key(account.game, account.account)] = account.to_dict()
    return {"schema_version": 1, "accounts": normalized}


def save_admins(path: Path, payload: dict[str, Any]) -> None:
    file_path = registry_path(path)
    file_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def add_admin(
    path: Path,
    *,
    account: str,
    display_name: str | None = None,
    roles: list[str] | None = None,
    game: str | None = None,
) -> dict[str, Any]:
    manifest = load_manifest(path)
    admin = AdminAccount(
        account=account,
        game=game or manifest.game,
        display_name=display_name or account,
        roles=roles or ["admin"],
    )
    payload = load_admins(path)
    payload["accounts"][_account_key(admin.game, admin.account)] = admin.to_dict()
    save_admins(path, payload)
    return admin.to_dict()


def remove_admin(path: Path, *, account: str, game: str | None = None) -> dict[str, Any]:
    manifest = load_manifest(path)
    payload = load_admins(path)
    key = _account_key(game or manifest.game, account)
    removed = payload["accounts"].pop(key, None)
    save_admins(path, payload)
    return {"removed": removed is not None, "account": account, "game": game or manifest.game}


def list_admins(path: Path) -> list[dict[str, Any]]:
    payload = load_admins(path)
    return sorted(
        payload["accounts"].values(),
        key=lambda account: (account["game"].lower(), account["account"].lower()),
    )


def is_admin(path: Path, *, account: str, game: str | None = None) -> bool:
    manifest = load_manifest(path)
    payload = load_admins(path)
    key = _account_key(game or manifest.game, account)
    admin = payload["accounts"].get(key)
    return bool(admin and admin.get("active", True))


def _account_key(game: str, account: str) -> str:
    return f"{game.strip().lower()}:{account.strip().lower()}"


def _required_string(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} is required")
    return value.strip()
