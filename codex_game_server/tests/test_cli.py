from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from codex_game_server.cli import main


class CliTests(unittest.TestCase):
    def test_init_and_inspect_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "survival"

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        "init",
                        str(root),
                        "--name",
                        "survival",
                        "--game",
                        "minecraft",
                        "--port",
                        "25565",
                        "--start-command",
                        "python -m http.server 25565",
                        "--json",
                    ]
                )

            self.assertEqual(exit_code, 0)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["server"]["name"], "survival")

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(["inspect", str(root), "--json"])

            self.assertEqual(exit_code, 0)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["plugin_count"], 0)
            self.assertTrue(payload["directories"]["world"]["exists"])

    def test_run_dry_run_prints_command(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "server"
            with redirect_stdout(io.StringIO()):
                main(["init", str(root), "--start-command", "python -m http.server 25565"])

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(["run", str(root), "--dry-run", "--json"])

            self.assertEqual(exit_code, 0)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["argv"], ["python", "-m", "http.server", "25565"])


if __name__ == "__main__":
    unittest.main()
