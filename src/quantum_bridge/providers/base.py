from __future__ import annotations

from abc import ABC, abstractmethod

from quantum_bridge.models import Allocation, ProviderCapability, ResourceSpec, RunResult


class ProviderAdapter(ABC):
    """Adapter contract for quantum runtime providers."""

    name: str

    @abstractmethod
    def capabilities(self) -> ProviderCapability:
        raise NotImplementedError

    @abstractmethod
    def allocate(self, spec: ResourceSpec) -> Allocation:
        raise NotImplementedError

    @abstractmethod
    def run_qasm(self, qasm: str, spec: ResourceSpec, allocation: Allocation) -> RunResult:
        raise NotImplementedError
