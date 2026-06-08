from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from codex_game_server.game_support import SUPPORTED_GAMES
from codex_game_server.manifest import load_manifest
from codex_game_server.operations import init_server, scaffold_integration, supported_games


class GameSupportTests(unittest.TestCase):
    def test_supported_targets_include_games_and_development_tools(self) -> None:
        payload = supported_games()
        games = {game["game"] for game in payload["games"]}

        self.assertEqual(
            {
                "minecraft",
                "project_zomboid",
                "palworld",
                "terraria",
                "roblox",
                "mapleworld",
                "unity",
                "unreal",
            },
            games,
        )
        categories = {game["category"] for game in payload["games"]}
        self.assertIn("development_tool", categories)
        self.assertIn("game_engine", categories)
        for game in payload["games"]:
            self.assertEqual(game["commands"]["codex"], "/codex *")
            self.assertEqual(game["commands"]["codex_func"], "/codex_func *")

    def test_init_uses_game_specific_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "pz"
            init_server(root, game="project-zomboid")

            manifest = load_manifest(root)

            self.assertEqual(manifest.game, "project_zomboid")
            self.assertEqual(manifest.port, SUPPORTED_GAMES["project_zomboid"].default_port)
            self.assertEqual(manifest.directories["plugins"], "mods")
            self.assertEqual(manifest.codex_settings["command_prefix"], "/codex")

    def test_init_accepts_development_tool_aliases(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "ue"
            init_server(root, game="unreal-engine")

            manifest = load_manifest(root)

            self.assertEqual(manifest.game, "unreal")
            self.assertEqual(manifest.directories["plugins"], "Plugins/CodexGameServer")

    def test_scaffold_generates_command_bridge_files_for_each_supported_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            for game in SUPPORTED_GAMES:
                root = base / game
                init_server(root, game=game)
                payload = scaffold_integration(root)
                files = [Path(item["path"]) for item in payload["files"]]
                contents = "\n".join(path.read_text(encoding="utf-8") for path in files)

                self.assertIn("/codex", contents)
                self.assertIn("/codex_func", contents)
                self.assertEqual(payload["game"], game)


if __name__ == "__main__":
    unittest.main()
