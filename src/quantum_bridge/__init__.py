"""Provider-neutral bridge for quantum runtime resources."""

from quantum_bridge.client import BridgeClient
from quantum_bridge.advisor import advise_sessions, algorithm_catalog_payload
from quantum_bridge.models import (
    Allocation,
    JobStatus,
    ProviderCapability,
    ResourceSpec,
    RunResult,
)

__all__ = [
    "Allocation",
    "BridgeClient",
    "JobStatus",
    "ProviderCapability",
    "ResourceSpec",
    "RunResult",
    "advise_sessions",
    "algorithm_catalog_payload",
]

__version__ = "0.1.0"
