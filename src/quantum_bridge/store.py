from __future__ import annotations

import json
import os
from pathlib import Path

from quantum_bridge.models import RunResult


class JobStore:
    """Small JSON job store used by the CLI."""

    def __init__(self, home: str | Path | None = None) -> None:
        root = home or os.environ.get("QUANTUM_BRIDGE_HOME") or Path.home() / ".quantum_bridge"
        self.root = Path(root)
        self.jobs_dir = self.root / "jobs"

    def save_result(self, result: RunResult) -> Path:
        self.jobs_dir.mkdir(parents=True, exist_ok=True)
        path = self._path_for(result.job_id)
        path.write_text(
            json.dumps(result.to_dict(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return path

    def load_result(self, job_id: str) -> RunResult:
        path = self._path_for(job_id)
        if not path.exists():
            raise FileNotFoundError(f"job '{job_id}' was not found in {self.jobs_dir}")

        data = json.loads(path.read_text(encoding="utf-8"))
        return RunResult.from_dict(data)

    def _path_for(self, job_id: str) -> Path:
        if "/" in job_id or "\\" in job_id:
            raise ValueError("job_id must not contain path separators")
        return self.jobs_dir / f"{job_id}.json"
