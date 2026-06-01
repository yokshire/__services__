# Architecture

Quantum Bridge is designed as a small runtime allocation layer between ordinary software and quantum computing providers.

## Core Concepts

`ResourceSpec` describes the requested runtime resource. It includes the provider name, optional backend, qubit count, shot count, priority, cost hints, and metadata.

`BridgeClient` is the SDK entrypoint. Applications use it to register providers, request allocations, and submit circuit payloads.

`ProviderAdapter` is the runtime boundary. Each quantum provider implements this contract so the rest of the system can remain provider-neutral.

`RunResult` is the normalized result returned to callers. It includes job id, status, provider, backend, shots, counts, timestamps, and provider metadata.

`JobStore` persists completed CLI runs as JSON. It is intentionally simple and local-first for the MVP.

`AlgorithmProfile` describes a known quantum algorithm family, the part of computation it may accelerate, migration constraints, payload shape, platform options, and references.

`advise_sessions` is the demo planner. It accepts project computation session metadata and returns candidate algorithms, replacement strategies, migration tool names, platform options, and missing API key prompts.

## Runtime Flow

```text
Application or CLI
  |
  | ResourceSpec + OpenQASM payload
  v
BridgeClient
  |
  | allocate()
  v
ProviderAdapter
  |
  | run_qasm()
  v
RunResult
  |
  +-- returned to caller
  +-- optionally persisted by JobStore
```

## Demo Advisor Flow

```text
Project computation sessions JSON
  |
  | session id, operation, tags, workload size, code entrypoint
  v
Demo Advisor API
  |
  | scores known quantum algorithm profiles
  v
Migration recommendation
  |
  +-- algorithm family
  +-- accelerated computation area
  +-- replacement strategy
  +-- migration tool shape
  +-- platform options
  +-- credential/API-key prompt
```

The advisor is intentionally conservative. It identifies candidates and prompts for credentials; it does not claim the selected algorithm will outperform the existing classical implementation.

## Provider Strategy

The core package must remain dependency-light. Provider SDK integrations should be added as optional adapters so that a basic install still works on any machine.

Planned adapter categories:

- local simulation for development and tests
- hosted quantum runtimes such as IBM/Qiskit Runtime
- cloud brokers such as AWS Braket
- organization-specific internal quantum runtimes
- specialized annealing or hybrid optimization services

## API Key Flow

The demo does not collect or store secrets. It reports which environment variables a service should request from the user:

- `IBM_QUANTUM_TOKEN` for IBM Quantum
- `AWS_PROFILE` or `AWS_ACCESS_KEY_ID` plus `AWS_SECRET_ACCESS_KEY` for AWS Braket
- Azure service principal variables for Azure Quantum
- `DWAVE_API_TOKEN` for D-Wave Leap

Provider adapters should check credentials at runtime and must avoid returning secret values in API responses.

## Open Questions

- How should long-running cloud jobs be resumed across machines?
- Should provider adapters expose queue estimates and cost estimates in a common format?
- Which payload formats should become first-class beyond OpenQASM 2?
- Should the bridge expose a local daemon API for non-Python applications?
- How much static code analysis should be added before the advisor recommends a migration?
