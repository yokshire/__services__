# Contributing

Quantum Bridge is at the pre-alpha stage. Contributions should keep the provider boundary small and stable.

## Development

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
python -m unittest discover -s tests
```

## Provider Adapters

Provider adapters should implement `ProviderAdapter` and avoid leaking provider-specific concepts into `BridgeClient`.

Keep provider credentials out of code and tests. Use environment variables or provider SDK configuration files.

## Pull Requests

- Include tests for bridge behavior or provider adapter contracts.
- Keep provider SDK dependencies optional unless they are required by the core package.
- Update `README.md` or `docs/architecture.md` when the public interface changes.
