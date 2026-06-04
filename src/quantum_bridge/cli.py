from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from quantum_bridge.advisor import DEMO_SESSIONS, advise_sessions, algorithm_catalog_payload
from quantum_bridge.api import run_api_server
from quantum_bridge.client import BridgeClient
from quantum_bridge.models import JobStatus, ResourceSpec, RunResult
from quantum_bridge.store import JobStore


EXAMPLE_REGISTRY: tuple[dict[str, str], ...] = (
    {
        "id": "bell-qasm",
        "path": "examples/bell.qasm",
        "command": "qb run examples/bell.qasm --shots 1000 --seed 7",
        "description": "Bell-state OpenQASM 2 circuit for checking the local simulator.",
    },
    {
        "id": "project-sessions",
        "path": "examples/project_sessions.json",
        "command": "qb advise examples/project_sessions.json --platform ibm_quantum",
        "description": "Three sample computation sessions for the demo migration advisor.",
    },
    {
        "id": "built-in-demo",
        "path": "built-in",
        "command": "qb demo",
        "description": "Built-in advisor demo using the same session shapes without a file.",
    },
)


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        return args.func(args)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="quantum-bridge",
        description="Allocate and run quantum runtime jobs through provider adapters.",
    )
    subcommands = parser.add_subparsers(dest="command", required=True)

    providers = subcommands.add_parser("providers", help="list registered providers")
    providers.add_argument("--json", action="store_true", help="print JSON")
    providers.set_defaults(func=_cmd_providers)

    examples = subcommands.add_parser("examples", help="list bundled examples and demo commands")
    examples.add_argument("--json", action="store_true", help="print JSON")
    examples.set_defaults(func=_cmd_examples)

    algorithms = subcommands.add_parser("algorithms", help="list quantum algorithm migration guidance")
    algorithms.add_argument("--json", action="store_true", help="print JSON")
    algorithms.set_defaults(func=_cmd_algorithms)

    advise = subcommands.add_parser("advise", help="advise quantum algorithm migrations for project sessions")
    advise.add_argument("sessions", help="JSON file containing a sessions list")
    advise.add_argument("--platform", default=None, help="preferred quantum hardware platform id")
    advise.add_argument("--max-candidates", type=int, default=3, help="maximum candidates per session")
    advise.add_argument("--include-low-confidence", action="store_true", help="include weak matches")
    advise.add_argument("--json", action="store_true", help="print JSON")
    advise.set_defaults(func=_cmd_advise)

    demo = subcommands.add_parser("demo", help="run the demo advisor against built-in project sessions")
    demo.add_argument("--platform", default="ibm_quantum", help="preferred quantum hardware platform id")
    demo.add_argument("--json", action="store_true", help="print JSON")
    demo.set_defaults(func=_cmd_demo)

    api = subcommands.add_parser("api", help="run the demo advisor HTTP API")
    api.add_argument("--host", default="127.0.0.1", help="bind host")
    api.add_argument("--port", type=int, default=8765, help="bind port")
    api.set_defaults(func=_cmd_api)

    run = subcommands.add_parser("run", help="run an OpenQASM 2 circuit")
    run.add_argument("circuit", help="path to an OpenQASM 2 file")
    run.add_argument("--shots", type=int, default=1024, help="number of measurement shots")
    run.add_argument("--qubits", type=int, default=None, help="requested qubit allocation")
    run.add_argument("--provider", default="local", help="provider adapter name")
    run.add_argument("--backend", default=None, help="provider backend name")
    run.add_argument("--priority", default="normal", help="runtime priority hint")
    run.add_argument("--max-cost-usd", type=float, default=None, help="maximum cost hint")
    run.add_argument("--seed", type=int, default=None, help="deterministic simulator seed")
    run.add_argument("--no-store", action="store_true", help="do not store the result locally")
    run.add_argument("--json", action="store_true", help="print JSON")
    run.set_defaults(func=_cmd_run)

    status = subcommands.add_parser("status", help="show a stored job status")
    status.add_argument("job_id")
    status.add_argument("--json", action="store_true", help="print JSON")
    status.set_defaults(func=_cmd_status)

    result = subcommands.add_parser("result", help="show a stored job result")
    result.add_argument("job_id")
    result.add_argument("--json", action="store_true", help="print JSON")
    result.set_defaults(func=_cmd_result)

    return parser


def _cmd_examples(args: argparse.Namespace) -> int:
    payload = {"examples": list(EXAMPLE_REGISTRY)}
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    print("Quantum Bridge examples")
    for example in EXAMPLE_REGISTRY:
        print("")
        print(f"{example['id']}")
        print(f"  path: {example['path']}")
        print(f"  purpose: {example['description']}")
        print(f"  try: {example['command']}")
    return 0


def _cmd_providers(args: argparse.Namespace) -> int:
    client = BridgeClient()
    capabilities = [capability.to_dict() for capability in client.capabilities()]

    if args.json:
        print(json.dumps(capabilities, indent=2, sort_keys=True))
        return 0

    for capability in capabilities:
        payloads = ", ".join(capability["supported_payloads"])
        backends = ", ".join(capability["backends"])
        print(f"{capability['name']} {capability['provider_version']}")
        print(f"  max_qubits: {capability['max_qubits']}")
        print(f"  payloads: {payloads}")
        print(f"  backends: {backends}")
        print(f"  async_jobs: {capability['supports_async_jobs']}")
        if capability["notes"]:
            print(f"  notes: {capability['notes']}")
    return 0


def _cmd_algorithms(args: argparse.Namespace) -> int:
    payload = algorithm_catalog_payload()
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    print("Quantum Bridge algorithm catalog")
    print("demo: true")
    print(payload["notice"])
    for algorithm in payload["algorithms"]:
        print("")
        print(f"{algorithm['id']}: {algorithm['name']}")
        print(f"  speedup: {algorithm['speedup_summary']}")
        print(f"  accelerates: {algorithm['acceleration_focus']}")
        print(f"  readiness: {algorithm['hardware_readiness']}")
        print(f"  migration_tools: {', '.join(algorithm['migration_tools'])}")
    return 0


def _cmd_advise(args: argparse.Namespace) -> int:
    payload = json.loads(Path(args.sessions).read_text(encoding="utf-8"))
    sessions = payload.get("sessions")
    if not isinstance(sessions, list):
        raise ValueError("sessions JSON must include a 'sessions' list")

    preferred_platform = args.platform or payload.get("preferred_platform")
    result = advise_sessions(
        sessions,
        preferred_platform=preferred_platform,
        max_candidates=args.max_candidates,
        include_low_confidence=args.include_low_confidence,
    )
    _print_advice(result, as_json=args.json)
    return 0


def _cmd_demo(args: argparse.Namespace) -> int:
    result = advise_sessions(DEMO_SESSIONS, preferred_platform=args.platform)
    _print_advice(result, as_json=args.json)
    return 0


def _cmd_api(args: argparse.Namespace) -> int:
    run_api_server(host=args.host, port=args.port)
    return 0


def _cmd_run(args: argparse.Namespace) -> int:
    qasm = Path(args.circuit).read_text(encoding="utf-8")
    metadata: dict[str, Any] = {}
    if args.seed is not None:
        metadata["seed"] = args.seed

    spec = ResourceSpec(
        qubits=args.qubits,
        shots=args.shots,
        provider=args.provider,
        backend=args.backend,
        priority=args.priority,
        max_cost_usd=args.max_cost_usd,
        metadata=metadata,
    )

    result = BridgeClient().run_qasm(qasm, spec, persist=not args.no_store)
    _print_result(result, as_json=args.json)
    return 0 if result.status == JobStatus.COMPLETED else 1


def _cmd_status(args: argparse.Namespace) -> int:
    result = JobStore().load_result(args.job_id)
    if args.json:
        print(json.dumps(_status_payload(result), indent=2, sort_keys=True))
    else:
        print(f"{result.job_id}: {result.status.value}")
        if result.error:
            print(f"error: {result.error}")
    return 0 if result.status == JobStatus.COMPLETED else 1


def _cmd_result(args: argparse.Namespace) -> int:
    result = JobStore().load_result(args.job_id)
    _print_result(result, as_json=args.json)
    return 0 if result.status == JobStatus.COMPLETED else 1


def _print_result(result: RunResult, *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
        return

    print(f"job_id: {result.job_id}")
    print(f"status: {result.status.value}")
    print(f"provider: {result.provider}")
    print(f"backend: {result.backend}")
    print(f"shots: {result.shots}")
    if result.error:
        print(f"error: {result.error}")
        return

    print("counts:")
    for bitstring, count in result.counts.items():
        print(f"  {bitstring}: {count}")


def _status_payload(result: RunResult) -> dict[str, Any]:
    return {
        "job_id": result.job_id,
        "status": result.status.value,
        "provider": result.provider,
        "backend": result.backend,
        "submitted_at": result.submitted_at,
        "completed_at": result.completed_at,
        "error": result.error,
    }


def _print_advice(result: dict[str, Any], *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return

    print("Quantum Bridge migration advisor")
    print("demo: true")
    print(result["notice"])
    print(
        "summary: "
        f"{result['summary']['sessions_with_candidates']}/"
        f"{result['summary']['sessions_received']} sessions matched"
    )

    for recommendation in result["recommendations"]:
        session = recommendation["session"]
        print("")
        print(f"session: {session['session_id']} - {session['name']}")
        for index, candidate in enumerate(recommendation["candidates"], start=1):
            algorithm = candidate["algorithm"]
            print(f"  {index}. {algorithm['name']} ({candidate['confidence']}, score {candidate['score']})")
            print(f"     migration_tool: {candidate['migration_tool']}")
            print(f"     replaces: {candidate['replacement_strategy']}")
            print(f"     platform_options: {', '.join(platform['id'] for platform in candidate['platform_options'])}")
            if candidate["auth_request"]["required"]:
                print(f"     auth: {candidate['auth_request']['message']}")

    if result["unmatched_sessions"]:
        print("")
        print("unmatched_sessions:")
        for session in result["unmatched_sessions"]:
            print(f"  {session['session_id']}: {session['reason']}")
