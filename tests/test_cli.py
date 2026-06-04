from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stdout

from quantum_bridge.cli import main


class CliTests(unittest.TestCase):
    def test_examples_command_lists_bundled_examples(self) -> None:
        stdout = io.StringIO()

        with redirect_stdout(stdout):
            exit_code = main(["examples", "--json"])

        self.assertEqual(exit_code, 0)
        payload = json.loads(stdout.getvalue())
        example_ids = {example["id"] for example in payload["examples"]}

        self.assertIn("bell-qasm", example_ids)
        self.assertIn("project-sessions", example_ids)
        self.assertIn("built-in-demo", example_ids)


if __name__ == "__main__":
    unittest.main()
