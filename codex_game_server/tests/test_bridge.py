from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from codex_game_server.accounts import add_admin, is_admin, list_admins, remove_admin
from codex_game_server.bridge import codex_func_request, codex_request
from codex_game_server.operations import init_server


class BridgeTests(unittest.TestCase):
    def test_admin_registry_authorizes_in_game_account(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "server"
            init_server(root, game="minecraft")

            admin = add_admin(root, account="Steve", display_name="Server Owner")

            self.assertEqual(admin["game"], "minecraft")
            self.assertTrue(is_admin(root, account="Steve"))
            self.assertEqual(list_admins(root)[0]["display_name"], "Server Owner")

            removed = remove_admin(root, account="Steve")
            self.assertTrue(removed["removed"])
            self.assertFalse(is_admin(root, account="Steve"))

    def test_codex_prompt_requires_registered_admin(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "server"
            init_server(root, game="minecraft")

            denied = codex_request(root, account="Guest", prompt="hello", dry_run=True)

            self.assertFalse(denied["ok"])
            self.assertEqual(denied["status"], "unauthorized")

    def test_codex_prompt_dry_run_accepts_registered_admin(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "server"
            init_server(root, game="minecraft")
            add_admin(root, account="Steve")

            accepted = codex_request(root, account="Steve", prompt="summarize server status", dry_run=True)

            self.assertTrue(accepted["ok"])
            self.assertEqual(accepted["status"], "dry_run")
            self.assertIn("summarize server status", accepted["message"])

    def test_codex_func_status_uses_internal_command_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "server"
            init_server(root, game="terraria")
            add_admin(root, account="Builder")

            payload = codex_func_request(root, account="Builder", command="status")

            self.assertTrue(payload["ok"])
            self.assertEqual(payload["data"]["game"], "terraria")


if __name__ == "__main__":
    unittest.main()
