# __services__

This repository is a workspace for small open-source service tools.

## Subprojects

- `quantum_runtime_bridge`: demo quantum runtime bridge for allocating quantum computing resources and advising algorithm migration candidates.
- `codex_game_server`: dependency-free Python bridge that lets trusted in-game or editor-side admins call Codex through game, platform, engine, and tool scaffolds.

## Quantum Runtime Bridge

```bash
cd quantum_runtime_bridge  # if this checkout keeps the project in a subdirectory
python -m pip install -e .
qb examples
qb run examples/bell.qasm --shots 1000 --seed 7
qb advise examples/project_sessions.json --platform ibm_quantum
```

Some repository checkouts keep the Quantum Runtime Bridge package at the root.
In that case, run the same commands from the repository root.

## Codex Game Server

```bash
cd codex_game_server
python -m pip install -e .
cgs codex status
cgs init ./servers/survival --name survival --game minecraft --port 25565
cgs targets
cgs admin add ./servers/survival --account Steve
cgs integrate ./servers/survival
cgs bridge prompt ./servers/survival --account Steve --prompt "Check this setup" --dry-run
```

See [codex_game_server/README.md](codex_game_server/README.md) for full details.
