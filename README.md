# Quantum Bridge

Quantum Bridge is an open-source bridge tool for allocating quantum computer runtime resources from other programs.

This repository is currently a demo. It does not claim production quantum speedup or execute real cloud quantum hardware yet.

The project goal is to give application developers a small, provider-neutral interface:

- request a quantum runtime resource with a clear `ResourceSpec`
- submit a circuit payload, starting with OpenQASM 2
- receive job status and measurement results through a stable SDK or CLI
- swap local simulation, cloud quantum runtimes, and future providers behind one adapter boundary
- ask a demo advisor API which known quantum algorithm family may fit a project computation session
- identify the quantum hardware platform credentials the service must request from the user

This repository starts with a dependency-free Python MVP. It includes a local OpenQASM simulator so anyone can install the tool and run a Bell-state circuit without needing cloud credentials.

## Install For Development

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
```

## Run The Example

```bash
quantum-bridge run examples/bell.qasm --shots 1000
```

Short alias:

```bash
qb run examples/bell.qasm --shots 1000
```

JSON output:

```bash
qb run examples/bell.qasm --shots 1000 --seed 7 --json
```

## Python SDK

```python
from quantum_bridge import BridgeClient, ResourceSpec

qasm = """
OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
creg c[2];
h q[0];
cx q[0], q[1];
measure q -> c;
"""

client = BridgeClient()
result = client.run_qasm(qasm, ResourceSpec(shots=1000, provider="local"))

print(result.counts)
```

## CLI

List providers:

```bash
qb providers
```

Run a circuit:

```bash
qb run examples/bell.qasm --shots 1000
```

Check a stored job:

```bash
qb status <job-id>
qb result <job-id>
```

By default, completed local jobs are stored under `~/.quantum_bridge/jobs`. Set `QUANTUM_BRIDGE_HOME` to change that location.

## Demo Migration Advisor

The demo advisor contains a small catalog of known quantum algorithm families and the parts of classical computation they may accelerate:

- Grover search for unstructured candidate search
- Quantum amplitude estimation for Monte Carlo-style sampling
- Shor period finding for factoring and discrete logarithms
- HHL-style linear systems under sparse/well-conditioned assumptions
- Hamiltonian simulation and phase estimation for quantum dynamics and spectral estimation
- VQE and QAOA for near-term hybrid demos
- Quantum annealing for QUBO/Ising binary optimization

Show the catalog:

```bash
qb algorithms
```

Run the built-in demo:

```bash
qb demo
```

Analyze project computation sessions from JSON:

```bash
qb advise examples/project_sessions.json --platform ibm_quantum
```

The advisor returns candidate algorithms, the computation session entrypoint to replace, the migration tool shape, platform choices, and API key environment variables to ask the user for. Example credential prompts include `IBM_QUANTUM_TOKEN`, AWS Braket credentials, Azure Quantum service principal variables, and `DWAVE_API_TOKEN`.

See [docs/quantum_algorithms.md](docs/quantum_algorithms.md) for the demo catalog and references.

## Demo API

Start the local HTTP API:

```bash
qb api --host 127.0.0.1 --port 8765
```

Endpoints:

- `GET /health`
- `GET /algorithms`
- `GET /demo`
- `POST /advise`

Example request:

```bash
curl -s http://127.0.0.1:8765/advise \
  -H 'Content-Type: application/json' \
  -d @examples/project_sessions.json
```

The API is intentionally local and demo-scoped. It decides which quantum algorithm family looks applicable; future provider adapters will execute the selected bridge session on real quantum platforms after user credential setup.

## Architecture

Quantum Bridge is organized around a provider adapter boundary.

```text
Application
  |
  | SDK or CLI
  v
BridgeClient
  |
  | ResourceSpec + circuit payload
  v
ProviderAdapter
  |
  +-- LocalSimulatorProvider
  +-- Future IBM/Qiskit adapter
  +-- Future AWS Braket adapter
  +-- Future custom runtime adapter
```

The current MVP ships with:

- `BridgeClient`: SDK entrypoint for applications
- `ResourceSpec`: requested runtime shape, including shots, qubits, backend, priority, metadata
- `ProviderAdapter`: adapter contract for runtime providers
- `LocalSimulatorProvider`: dependency-free local simulator for OpenQASM 2 subset
- `JobStore`: local JSON result store for CLI status/result commands
- `AlgorithmProfile`: demo catalog entry for algorithm speedup area and migration constraints
- `advise_sessions`: demo planner for project computation sessions and platform credential prompts

See [docs/architecture.md](docs/architecture.md) for more detail.

## Supported OpenQASM 2 Subset

The local provider currently supports:

- declarations: `OPENQASM`, `include`, `qreg`, `creg`
- gates: `h`, `x`, `y`, `z`, `s`, `sdg`, `t`, `tdg`, `id`, `cx`
- measurement: `measure q -> c`, `measure q[i] -> c[j]`
- ignored no-op: `barrier`

This is enough for smoke testing bridge workflows. Production provider adapters should forward payloads to real runtimes rather than relying on the local simulator.

## Release Target

The GitHub release repository is:

https://github.com/yokshire/__services__

The included GitHub Actions workflows run unit tests and build release artifacts on version tags.

## License

MIT
