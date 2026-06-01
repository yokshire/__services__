from __future__ import annotations

from typing import Any

from quantum_bridge.models import (
    Allocation,
    JobStatus,
    ProviderCapability,
    ResourceSpec,
    RunResult,
    new_id,
    utc_now,
)
from quantum_bridge.providers.base import ProviderAdapter
from quantum_bridge.providers.qasm import simulate_counts


class LocalSimulatorProvider(ProviderAdapter):
    name = "local"
    provider_version = "0.1.0"

    def __init__(self, max_qubits: int = 16) -> None:
        self.max_qubits = max_qubits

    def capabilities(self) -> ProviderCapability:
        return ProviderCapability(
            name=self.name,
            provider_version=self.provider_version,
            max_qubits=self.max_qubits,
            supported_payloads=["openqasm2"],
            backends=["statevector"],
            supports_async_jobs=False,
            notes="Dependency-free local simulator for development and smoke tests.",
        )

    def allocate(self, spec: ResourceSpec) -> Allocation:
        backend = spec.backend or "statevector"
        if backend != "statevector":
            raise ValueError("local provider only supports the 'statevector' backend")
        if spec.qubits is not None and spec.qubits > self.max_qubits:
            raise ValueError(
                f"local provider supports up to {self.max_qubits} qubits; requested {spec.qubits}"
            )
        return Allocation(provider=self.name, backend=backend, spec=spec)

    def run_qasm(self, qasm: str, spec: ResourceSpec, allocation: Allocation) -> RunResult:
        submitted_at = utc_now()
        job_id = new_id("job")
        seed = _seed_from_metadata(spec.metadata)

        try:
            counts, circuit = simulate_counts(
                qasm,
                shots=spec.shots,
                seed=seed,
                max_qubits=self.max_qubits,
            )
            if spec.qubits is not None and circuit.num_qubits > spec.qubits:
                raise ValueError(
                    f"circuit requires {circuit.num_qubits} qubits; allocation requested {spec.qubits}"
                )
            return RunResult(
                job_id=job_id,
                status=JobStatus.COMPLETED,
                provider=self.name,
                backend=allocation.backend,
                shots=spec.shots,
                counts=counts,
                submitted_at=submitted_at,
                completed_at=utc_now(),
                allocation_id=allocation.allocation_id,
                metadata={
                    "payload": "openqasm2",
                    "qubits": circuit.num_qubits,
                    "clbits": circuit.num_clbits,
                    "seed": seed,
                },
            )
        except Exception as exc:
            return RunResult(
                job_id=job_id,
                status=JobStatus.FAILED,
                provider=self.name,
                backend=allocation.backend,
                shots=spec.shots,
                submitted_at=submitted_at,
                completed_at=utc_now(),
                allocation_id=allocation.allocation_id,
                error=str(exc),
                metadata={"payload": "openqasm2", "seed": seed},
            )


def _seed_from_metadata(metadata: dict[str, Any]) -> int | None:
    raw_seed = metadata.get("seed")
    if raw_seed is None:
        return None
    return int(raw_seed)
