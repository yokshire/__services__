from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex}"


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class ResourceSpec:
    qubits: int | None = None
    shots: int = 1024
    provider: str = "local"
    backend: str | None = None
    priority: str = "normal"
    max_cost_usd: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.qubits is not None and self.qubits < 1:
            raise ValueError("qubits must be greater than zero when provided")
        if self.shots < 1:
            raise ValueError("shots must be greater than zero")
        if not self.provider:
            raise ValueError("provider is required")
        if not isinstance(self.metadata, dict):
            raise TypeError("metadata must be a dictionary")


@dataclass(frozen=True)
class Allocation:
    provider: str
    backend: str
    spec: ResourceSpec
    allocation_id: str = field(default_factory=lambda: new_id("alloc"))
    created_at: str = field(default_factory=utc_now)


@dataclass(frozen=True)
class ProviderCapability:
    name: str
    provider_version: str
    max_qubits: int
    supported_payloads: list[str]
    backends: list[str]
    supports_async_jobs: bool = False
    notes: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RunResult:
    job_id: str
    status: JobStatus
    provider: str
    backend: str
    shots: int
    counts: dict[str, int] = field(default_factory=dict)
    submitted_at: str = field(default_factory=utc_now)
    completed_at: str | None = None
    allocation_id: str | None = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RunResult":
        values = dict(data)
        values["status"] = JobStatus(values["status"])
        return cls(**values)
