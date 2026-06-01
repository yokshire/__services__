from __future__ import annotations

import os
from dataclasses import asdict, dataclass, field
from typing import Any

from quantum_bridge.algorithms import (
    ALGORITHM_CATALOG,
    CATALOG_VERSION,
    PLATFORM_TARGETS,
    AlgorithmProfile,
    PlatformTarget,
)


DEMO_NOTICE = (
    "Demo advisor only. It identifies candidate quantum algorithm migrations and "
    "credential requirements; it does not prove production speedup or run cloud hardware."
)


DEMO_SESSIONS: tuple[dict[str, Any], ...] = (
    {
        "session_id": "risk-monte-carlo",
        "name": "Derivative risk Monte Carlo",
        "operation": "Estimate expected loss from many sampled market paths.",
        "tags": ["monte_carlo", "risk", "expectation", "finance"],
        "workload_size": 2500000,
        "current_runtime": "python/numpy",
        "code_entrypoint": "risk/simulate.py:run_paths",
    },
    {
        "session_id": "routing-optimizer",
        "name": "Fleet route optimizer",
        "operation": "Solve a QUBO-like combinatorial routing problem with binary decision variables.",
        "tags": ["optimization", "qubo", "routing", "constraint_optimization"],
        "workload_size": 18000,
        "current_runtime": "ortools",
        "code_entrypoint": "ops/routes.py:optimize",
    },
    {
        "session_id": "molecule-energy",
        "name": "Small molecule ground-state estimate",
        "operation": "Evaluate Hamiltonian expectation values for molecular energy search.",
        "tags": ["chemistry", "hamiltonian", "ground_state", "vqe"],
        "workload_size": 64,
        "current_runtime": "classical-simulator",
        "code_entrypoint": "chem/energy.py:estimate",
    },
)


@dataclass(frozen=True)
class ComputeSession:
    session_id: str
    name: str
    operation: str
    tags: tuple[str, ...] = ()
    workload_size: int | None = None
    current_runtime: str | None = None
    code_entrypoint: str | None = None
    constraints: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ComputeSession":
        session_id = str(data.get("session_id") or data.get("id") or data.get("name") or "session")
        raw_tags = data.get("tags", ())
        if isinstance(raw_tags, str):
            tags = tuple(part.strip() for part in raw_tags.split(",") if part.strip())
        else:
            tags = tuple(str(tag) for tag in raw_tags)

        workload_size = data.get("workload_size")
        if workload_size is not None:
            workload_size = int(workload_size)

        return cls(
            session_id=session_id,
            name=str(data.get("name") or session_id),
            operation=str(data.get("operation") or data.get("description") or ""),
            tags=tags,
            workload_size=workload_size,
            current_runtime=data.get("current_runtime"),
            code_entrypoint=data.get("code_entrypoint"),
            constraints=dict(data.get("constraints") or {}),
            metadata=dict(data.get("metadata") or {}),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def text(self) -> str:
        parts = [
            self.session_id,
            self.name,
            self.operation,
            self.current_runtime or "",
            self.code_entrypoint or "",
            " ".join(self.tags),
            " ".join(str(value) for value in self.constraints.values()),
        ]
        return _normalize(" ".join(parts))

    def tag_set(self) -> set[str]:
        tags: set[str] = set()
        for tag in self.tags:
            normalized = _normalize(tag)
            tags.add(normalized)
            tags.add(normalized.replace("_", " "))
        return tags


def advise_sessions(
    sessions: list[dict[str, Any]] | tuple[dict[str, Any], ...],
    *,
    preferred_platform: str | None = None,
    max_candidates: int = 3,
    include_low_confidence: bool = False,
) -> dict[str, Any]:
    parsed_sessions = [ComputeSession.from_dict(session) for session in sessions]
    recommendations = []
    unmatched_sessions = []

    for session in parsed_sessions:
        candidates = _rank_algorithms(session)
        if not include_low_confidence:
            candidates = [candidate for candidate in candidates if candidate["score"] >= 0.2]
        candidates = candidates[:max_candidates]

        if not candidates:
            unmatched_sessions.append(
                {
                    "session_id": session.session_id,
                    "name": session.name,
                    "reason": "No catalog algorithm matched the session signals strongly enough.",
                }
            )
            continue

        recommendation = {
            "session": session.to_dict(),
            "candidates": [
                _candidate_payload(session, candidate, preferred_platform=preferred_platform)
                for candidate in candidates
            ],
        }
        recommendations.append(recommendation)

    auth_requests = _aggregate_auth_requests(recommendations)

    return {
        "demo": True,
        "notice": DEMO_NOTICE,
        "catalog_version": CATALOG_VERSION,
        "summary": {
            "sessions_received": len(parsed_sessions),
            "sessions_with_candidates": len(recommendations),
            "unmatched_sessions": len(unmatched_sessions),
        },
        "recommendations": recommendations,
        "unmatched_sessions": unmatched_sessions,
        "auth_requests": auth_requests,
    }


def algorithm_catalog_payload() -> dict[str, Any]:
    return {
        "demo": True,
        "notice": DEMO_NOTICE,
        "catalog_version": CATALOG_VERSION,
        "algorithms": [profile.to_dict() for profile in ALGORITHM_CATALOG],
        "platforms": [target.to_dict() for target in PLATFORM_TARGETS],
    }


def _rank_algorithms(session: ComputeSession) -> list[dict[str, Any]]:
    ranked = []
    for profile in ALGORITHM_CATALOG:
        score, evidence = _score_profile(session, profile)
        if score <= 0:
            continue
        ranked.append(
            {
                "algorithm": profile,
                "score": score,
                "confidence": _confidence(score),
                "evidence": evidence,
            }
        )
    return sorted(ranked, key=lambda item: item["score"], reverse=True)


def _score_profile(session: ComputeSession, profile: AlgorithmProfile) -> tuple[float, list[str]]:
    text = session.text()
    tags = session.tag_set()
    evidence: list[str] = []
    score = 0.0

    for term in profile.problem_tags:
        if _term_matches(term, text, tags):
            evidence.append(f"matched problem tag '{term}'")
            score += 0.13

    for signal in profile.session_signals:
        if _term_matches(signal, text, tags):
            evidence.append(f"matched session signal '{signal}'")
            score += 0.1

    if session.workload_size is not None:
        if session.workload_size >= 1_000_000:
            evidence.append("large repeated workload size")
            score += 0.12
        elif session.workload_size >= 10_000:
            evidence.append("moderate repeated workload size")
            score += 0.06

    if session.constraints.get("requires_exact_result") and profile.speedup_type.startswith("heuristic"):
        evidence.append("penalized heuristic candidate because exact result is required")
        score -= 0.12

    return max(0.0, min(score, 1.0)), evidence


def _candidate_payload(
    session: ComputeSession,
    candidate: dict[str, Any],
    *,
    preferred_platform: str | None,
) -> dict[str, Any]:
    profile: AlgorithmProfile = candidate["algorithm"]
    platforms = _platform_payloads(profile, preferred_platform=preferred_platform)
    best_platform = platforms[0] if platforms else None
    requires_auth = any(platform["auth"]["required"] for platform in platforms if platform["id"] != "local")

    return {
        "algorithm": profile.to_dict(),
        "score": round(candidate["score"], 3),
        "confidence": candidate["confidence"],
        "why": candidate["evidence"][:6],
        "migration_tool": profile.migration_tools[0],
        "replacement_strategy": _replacement_strategy(session, profile),
        "bridge_session": {
            "session_id": session.session_id,
            "payload_hint": profile.payload_hint,
            "resource_spec": {
                "provider": "local" if best_platform and best_platform["id"] == "local" else "external",
                "backend": best_platform["id"] if best_platform else None,
                "shots": 1024,
                "metadata": {
                    "demo": True,
                    "algorithm_id": profile.id,
                    "migration_tool": profile.migration_tools[0],
                },
            },
        },
        "platform_options": platforms,
        "auth_request": {
            "required": requires_auth,
            "message": _auth_message(platforms),
        },
    }


def _platform_payloads(
    profile: AlgorithmProfile,
    *,
    preferred_platform: str | None,
) -> list[dict[str, Any]]:
    targets = [target for target in PLATFORM_TARGETS if target.id in profile.platform_ids]
    if preferred_platform:
        targets = sorted(targets, key=lambda target: 0 if target.id == preferred_platform else 1)

    return [_platform_payload(target) for target in targets]


def _platform_payload(target: PlatformTarget) -> dict[str, Any]:
    configured_group = _configured_credential_group(target)
    credential_groups = [list(group) for group in target.credential_env_groups]
    return {
        "id": target.id,
        "name": target.name,
        "runtime": target.runtime,
        "readiness": target.readiness,
        "auth": {
            "required": bool(target.credential_env_groups) and configured_group is None,
            "configured": configured_group is not None or not target.credential_env_groups,
            "accepted_env_groups": credential_groups,
            "configured_env_group": list(configured_group) if configured_group else [],
            "prompt": target.auth_note,
        },
    }


def _configured_credential_group(target: PlatformTarget) -> tuple[str, ...] | None:
    if not target.credential_env_groups:
        return ()
    for group in target.credential_env_groups:
        if all(os.environ.get(name) for name in group):
            return group
    return None


def _replacement_strategy(session: ComputeSession, profile: AlgorithmProfile) -> str:
    strategy_by_family = {
        "amplitude_amplification": "Extract the predicate/candidate checker from the classical session and wrap it as a reversible oracle circuit.",
        "amplitude_estimation": "Replace repeated sampling with a state-preparation plus estimator loop while keeping classical preprocessing and reporting.",
        "period_finding": "Keep classical input/output handling and replace only the period-finding core with a quantum circuit template.",
        "linear_algebra": "Keep matrix assembly classical and route sparse/block-encoded solve observables through a quantum linear-system subroutine.",
        "quantum_simulation": "Translate model Hamiltonian terms into a provider payload and run simulation/estimation as a bridge-managed session.",
        "spectral_estimation": "Wrap the unitary or simulator kernel as a controlled operation and call phase estimation for spectral outputs.",
        "hybrid_variational": "Keep the optimizer loop in the host program and delegate circuit expectation evaluations through Quantum Bridge.",
        "annealing": "Normalize the optimization core to QUBO/Ising form and delegate sampling to an annealing provider adapter.",
    }
    base = strategy_by_family.get(profile.family, "Isolate the accelerated kernel and call it through Quantum Bridge.")
    if session.code_entrypoint:
        return f"{base} Candidate entrypoint: {session.code_entrypoint}."
    return base


def _auth_message(platforms: list[dict[str, Any]]) -> str:
    missing = [
        platform
        for platform in platforms
        if platform["id"] != "local" and platform["auth"]["required"]
    ]
    if not missing:
        return "No additional cloud credential is required for the selected configured/demo platform."

    parts = []
    for platform in missing:
        groups = [" + ".join(group) for group in platform["auth"]["accepted_env_groups"]]
        parts.append(f"{platform['name']}: provide one of [{'; '.join(groups)}]")
    return "Ask the user to choose a quantum hardware platform and provide credentials. " + " ".join(parts)


def _aggregate_auth_requests(recommendations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    requests: dict[str, dict[str, Any]] = {}
    for recommendation in recommendations:
        for candidate in recommendation["candidates"]:
            for platform in candidate["platform_options"]:
                if platform["id"] == "local" or not platform["auth"]["required"]:
                    continue
                requests[platform["id"]] = {
                    "platform_id": platform["id"],
                    "platform_name": platform["name"],
                    "accepted_env_groups": platform["auth"]["accepted_env_groups"],
                    "prompt": platform["auth"]["prompt"],
                }
    return list(requests.values())


def _confidence(score: float) -> str:
    if score >= 0.62:
        return "high"
    if score >= 0.36:
        return "medium"
    return "low"


def _term_matches(term: str, text: str, tags: set[str]) -> bool:
    normalized = _normalize(term)
    spaced = normalized.replace("_", " ")
    underscored = normalized.replace(" ", "_")
    return normalized in tags or spaced in tags or underscored in tags or spaced in text


def _normalize(value: str) -> str:
    return " ".join(value.lower().replace("-", " ").replace("_", " ").split())
