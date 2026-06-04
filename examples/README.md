# Examples

Quantum Bridge currently includes two file-based examples and one built-in CLI demo.

## `bell.qasm`

OpenQASM 2 Bell-state circuit for checking that the local simulator and bridge runtime path work.

```bash
qb run examples/bell.qasm --shots 1000 --seed 7
```

Expected behavior: the result counts contain only correlated states, usually `00` and `11`.

## `project_sessions.json`

Sample project computation sessions for the migration advisor. It includes:

- `risk-monte-carlo`: sampling-heavy finance/risk estimation
- `routing-optimizer`: QUBO-like routing optimization
- `molecule-energy`: Hamiltonian/VQE-style chemistry estimate

```bash
qb advise examples/project_sessions.json --platform ibm_quantum
```

Expected behavior: the advisor returns candidate quantum algorithm families, migration tool names, platform options, and API key prompts.

## Built-In Demo

The built-in demo runs without an input file.

```bash
qb demo
```

To list examples from the CLI:

```bash
qb examples
```
