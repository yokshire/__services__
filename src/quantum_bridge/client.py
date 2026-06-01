from __future__ import annotations

from quantum_bridge.models import Allocation, ProviderCapability, ResourceSpec, RunResult
from quantum_bridge.providers import LocalSimulatorProvider, ProviderAdapter
from quantum_bridge.store import JobStore


class BridgeClient:
    """SDK entrypoint for allocating quantum runtime resources."""

    def __init__(
        self,
        providers: list[ProviderAdapter] | None = None,
        store: JobStore | None = None,
    ) -> None:
        self._providers: dict[str, ProviderAdapter] = {}
        self.store = store if store is not None else JobStore()

        for provider in providers or [LocalSimulatorProvider()]:
            self.register_provider(provider)

    def register_provider(self, provider: ProviderAdapter) -> None:
        self._providers[provider.name] = provider

    def provider_names(self) -> list[str]:
        return sorted(self._providers)

    def capabilities(self) -> list[ProviderCapability]:
        return [self._providers[name].capabilities() for name in self.provider_names()]

    def allocate(self, spec: ResourceSpec) -> Allocation:
        return self._provider_for(spec).allocate(spec)

    def run_qasm(
        self,
        qasm: str,
        spec: ResourceSpec | None = None,
        *,
        persist: bool = True,
    ) -> RunResult:
        resolved_spec = spec if spec is not None else ResourceSpec()
        provider = self._provider_for(resolved_spec)
        allocation = provider.allocate(resolved_spec)
        result = provider.run_qasm(qasm, resolved_spec, allocation)

        if persist:
            self.store.save_result(result)

        return result

    def _provider_for(self, spec: ResourceSpec) -> ProviderAdapter:
        try:
            return self._providers[spec.provider]
        except KeyError as exc:
            available = ", ".join(self.provider_names()) or "none"
            raise ValueError(
                f"provider '{spec.provider}' is not registered; available providers: {available}"
            ) from exc
