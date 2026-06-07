from __future__ import annotations

import json
import socket
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

from codex_game_server.manifest import load_manifest
from codex_game_server.operations import (
    check_health,
    create_backup,
    init_server,
    inspect_server,
    list_plugins,
)


class OperationsTests(unittest.TestCase):
    def test_init_creates_manifest_and_directories(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "server"
            manifest = init_server(
                root,
                name="survival",
                game="minecraft",
                port=_free_port(),
                start_command=["python", "-m", "http.server", "25565"],
            )

            self.assertTrue(manifest.manifest_path.exists())
            self.assertTrue((root / "world").is_dir())
            self.assertTrue((root / "plugins").is_dir())
            loaded = load_manifest(root)
            self.assertEqual(loaded.name, "survival")

    def test_inspect_reports_plugins_and_backups(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "server"
            init_server(root, port=_free_port())
            (root / "plugins" / "example.jar").write_text("plugin", encoding="utf-8")
            (root / "world" / "level.dat").write_text("world", encoding="utf-8")
            create_backup(root, label="before update")

            payload = inspect_server(root)

            self.assertEqual(payload["plugin_count"], 1)
            self.assertEqual(payload["backup_count"], 1)
            self.assertEqual(list_plugins(root)[0]["name"], "example.jar")

    def test_backup_includes_world_files_and_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "server"
            init_server(root, name="server one", port=_free_port())
            (root / "world" / "level.dat").write_text("world", encoding="utf-8")

            payload = create_backup(root, label="night one")

            with ZipFile(payload["path"]) as archive:
                names = set(archive.namelist())
                manifest = json.loads(archive.read("_codex_game_server/server.json"))

            self.assertIn("world/level.dat", names)
            self.assertEqual(manifest["name"], "server one")
            self.assertEqual(payload["label"], "night-one")

    def test_health_reports_closed_free_port(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "server"
            port = _free_port()
            init_server(root, port=port)

            payload = check_health(root, timeout=0.1)

            self.assertEqual(payload["status"], "closed")
            self.assertEqual(payload["port"], port)


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


if __name__ == "__main__":
    unittest.main()
