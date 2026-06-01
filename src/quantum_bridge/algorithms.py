from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


CATALOG_VERSION = "demo-2026-06-01"


@dataclass(frozen=True)
class PlatformTarget:
    id: str
    name: str
    runtime: str
    credential_env_groups: tuple[tuple[str, ...], ...]
    auth_note: str
    readiness: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AlgorithmProfile:
    id: str
    name: str
    family: str
    speedup_type: str
    speedup_summary: str
    acceleration_focus: str
    problem_tags: tuple[str, ...]
    session_signals: tuple[str, ...]
    constraints: tuple[str, ...]
    hardware_readiness: str
    payload_hint: str
    migration_tools: tuple[str, ...]
    platform_ids: tuple[str, ...]
    references: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


PLATFORM_TARGETS: tuple[PlatformTarget, ...] = (
    PlatformTarget(
        id="local",
        name="Local simulator",
        runtime="Quantum Bridge local OpenQASM simulator",
        credential_env_groups=(),
        auth_note="No credentials required. Demo and smoke-test only.",
        readiness="demo_ready",
    ),
    PlatformTarget(
        id="ibm_quantum",
        name="IBM Quantum",
        runtime="Qiskit Runtime service adapter",
        credential_env_groups=(("IBM_QUANTUM_TOKEN",),),
        auth_note="Ask the user for an IBM Quantum API token and store it as IBM_QUANTUM_TOKEN.",
        readiness="adapter_planned",
    ),
    PlatformTarget(
        id="aws_braket",
        name="AWS Braket",
        runtime="AWS Braket managed quantum devices and simulators",
        credential_env_groups=(("AWS_PROFILE",), ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY")),
        auth_note="Ask the user for an AWS profile or access key pair with Braket permissions.",
        readiness="adapter_planned",
    ),
    PlatformTarget(
        id="azure_quantum",
        name="Azure Quantum",
        runtime="Azure Quantum workspace targets",
        credential_env_groups=(
            ("AZURE_CLIENT_ID", "AZURE_TENANT_ID", "AZURE_CLIENT_SECRET", "AZURE_SUBSCRIPTION_ID"),
        ),
        auth_note="Ask the user to authenticate an Azure Quantum workspace or provide service principal variables.",
        readiness="adapter_planned",
    ),
    PlatformTarget(
        id="dwave_leap",
        name="D-Wave Leap",
        runtime="D-Wave quantum annealing and hybrid solvers",
        credential_env_groups=(("DWAVE_API_TOKEN",),),
        auth_note="Ask the user for a D-Wave Leap API token and store it as DWAVE_API_TOKEN.",
        readiness="adapter_planned",
    ),
)


ALGORITHM_CATALOG: tuple[AlgorithmProfile, ...] = (
    AlgorithmProfile(
        id="grover_search",
        name="Grover search",
        family="amplitude_amplification",
        speedup_type="quadratic_query_speedup",
        speedup_summary="Unstructured search can move from O(N) oracle checks to O(sqrt(N)) oracle calls.",
        acceleration_focus="Repeated candidate testing where a reversible oracle can mark valid answers.",
        problem_tags=(
            "search",
            "unstructured_search",
            "bruteforce",
            "constraint_satisfaction",
            "oracle",
            "key_search",
        ),
        session_signals=(
            "scan candidates",
            "brute force",
            "find matching",
            "constraint filter",
            "oracle",
        ),
        constraints=(
            "Requires a reversible oracle for the target predicate.",
            "Useful speedup depends on oracle cost and hardware depth.",
            "Real advantage generally needs fault-tolerant hardware or a very small demo instance.",
        ),
        hardware_readiness="fault_tolerant_for_scale",
        payload_hint="oracle_circuit_openqasm2",
        migration_tools=("oracle-wrapper", "openqasm-runner"),
        platform_ids=("local", "ibm_quantum", "aws_braket", "azure_quantum"),
        references=("https://arxiv.org/abs/quant-ph/9605043",),
    ),
    AlgorithmProfile(
        id="amplitude_estimation",
        name="Quantum amplitude estimation",
        family="amplitude_estimation",
        speedup_type="quadratic_sampling_speedup",
        speedup_summary="Monte Carlo-style estimation can reduce sample complexity from O(1/epsilon^2) to O(1/epsilon) under oracle assumptions.",
        acceleration_focus="Probability, expectation, risk, integration, and simulation workloads dominated by repeated sampling.",
        problem_tags=(
            "monte_carlo",
            "sampling",
            "risk",
            "probability",
            "expectation",
            "integration",
            "finance",
        ),
        session_signals=(
            "monte carlo",
            "sample paths",
            "estimate probability",
            "expected value",
            "risk model",
            "numerical integration",
        ),
        constraints=(
            "Requires state preparation and payoff/probability oracles.",
            "Near-term variants may trade rigorous speedup for shallower circuits.",
            "Best candidate when sampling cost dominates the classical workload.",
        ),
        hardware_readiness="fault_tolerant_or_iterative_nisq",
        payload_hint="state_preparation_plus_estimator",
        migration_tools=("sampler-estimator-wrapper", "hybrid-estimation-loop"),
        platform_ids=("local", "ibm_quantum", "aws_braket", "azure_quantum"),
        references=("https://arxiv.org/abs/quant-ph/0005055",),
    ),
    AlgorithmProfile(
        id="shor_factoring",
        name="Shor factoring and discrete logarithm",
        family="period_finding",
        speedup_type="exponential_asymptotic_speedup",
        speedup_summary="Integer factoring and discrete logarithms move from sub-exponential classical methods to polynomial-time quantum algorithms.",
        acceleration_focus="Period finding for cryptanalytic factoring and discrete logarithm sessions.",
        problem_tags=(
            "factoring",
            "integer_factorization",
            "discrete_log",
            "cryptanalysis",
            "period_finding",
            "rsa",
        ),
        session_signals=(
            "factor integer",
            "discrete logarithm",
            "rsa",
            "period finding",
            "cryptanalysis",
        ),
        constraints=(
            "Not a practical replacement on current small noisy devices for real cryptographic sizes.",
            "Requires fault-tolerant circuits and many logical qubits at useful sizes.",
            "Demo instances can run only as educational circuits.",
        ),
        hardware_readiness="fault_tolerant_required",
        payload_hint="period_finding_circuit",
        migration_tools=("period-finding-template", "openqasm-runner"),
        platform_ids=("local", "ibm_quantum", "aws_braket", "azure_quantum"),
        references=("https://math.mit.edu/~shor/papers/algsfqc-dlf.pdf",),
    ),
    AlgorithmProfile(
        id="hhl_linear_systems",
        name="HHL linear systems",
        family="linear_algebra",
        speedup_type="exponential_under_assumptions",
        speedup_summary="Certain sparse, well-conditioned linear systems can yield exponential improvements for estimating properties of the solution state.",
        acceleration_focus="Linear solve sessions where only observables of the solution are needed, not the full vector output.",
        problem_tags=(
            "linear_system",
            "sparse_matrix",
            "matrix_inverse",
            "least_squares",
            "linear_algebra",
        ),
        session_signals=(
            "solve ax=b",
            "linear system",
            "sparse matrix",
            "matrix inverse",
            "condition number",
        ),
        constraints=(
            "Requires efficient state preparation and sparse Hamiltonian simulation.",
            "Returns a quantum state; reading the full solution can erase the advantage.",
            "Best for estimating observables or downstream quantum subroutines.",
        ),
        hardware_readiness="fault_tolerant_required_for_scale",
        payload_hint="block_encoding_or_sparse_matrix_oracle",
        migration_tools=("linear-system-oracle-wrapper", "hybrid-observable-estimator"),
        platform_ids=("local", "ibm_quantum", "aws_braket", "azure_quantum"),
        references=("https://arxiv.org/abs/0811.3171", "https://arxiv.org/abs/1802.08227"),
    ),
    AlgorithmProfile(
        id="hamiltonian_simulation",
        name="Hamiltonian and quantum dynamics simulation",
        family="quantum_simulation",
        speedup_type="natural_quantum_simulation",
        speedup_summary="Quantum systems with exponentially large Hilbert spaces can be represented directly on quantum hardware.",
        acceleration_focus="Chemistry, materials, many-body physics, and quantum dynamics sessions that classically expand exponentially.",
        problem_tags=(
            "hamiltonian",
            "quantum_simulation",
            "chemistry",
            "materials",
            "many_body",
            "dynamics",
        ),
        session_signals=(
            "hamiltonian",
            "quantum dynamics",
            "many body",
            "molecular energy",
            "materials simulation",
        ),
        constraints=(
            "Problem encoding and error rates dominate practical usefulness.",
            "Near-term runs are usually small demonstrations or hybrid workflows.",
            "Fault-tolerant phase estimation is needed for high-precision production workloads.",
        ),
        hardware_readiness="nisq_demo_to_fault_tolerant",
        payload_hint="hamiltonian_terms",
        migration_tools=("hamiltonian-term-translator", "time-evolution-runner"),
        platform_ids=("local", "ibm_quantum", "aws_braket", "azure_quantum"),
        references=("https://pubmed.ncbi.nlm.nih.gov/8688088/", "https://philpapers.org/rec/FEYSPW"),
    ),
    AlgorithmProfile(
        id="quantum_phase_estimation",
        name="Quantum phase estimation",
        family="spectral_estimation",
        speedup_type="core_subroutine",
        speedup_summary="Phase estimation extracts eigenphase information and underpins factoring, chemistry, and linear-system algorithms.",
        acceleration_focus="Eigenvalue, frequency, phase, and spectral estimation sessions with unitary simulation access.",
        problem_tags=(
            "eigenvalue",
            "phase",
            "spectral",
            "frequency",
            "operator_estimation",
            "chemistry_precision",
        ),
        session_signals=(
            "eigenvalue",
            "phase estimate",
            "spectral",
            "frequency estimate",
            "operator eigen",
        ),
        constraints=(
            "Requires controlled unitary operations.",
            "High precision generally requires deep circuits.",
            "Often appears as a subroutine rather than a standalone migration target.",
        ),
        hardware_readiness="fault_tolerant_for_precision",
        payload_hint="controlled_unitary",
        migration_tools=("controlled-unitary-wrapper", "phase-estimation-template"),
        platform_ids=("local", "ibm_quantum", "aws_braket", "azure_quantum"),
        references=("https://arxiv.org/abs/quant-ph/9511026",),
    ),
    AlgorithmProfile(
        id="vqe",
        name="Variational quantum eigensolver",
        family="hybrid_variational",
        speedup_type="heuristic_near_term",
        speedup_summary="VQE targets ground-state energy and related Hamiltonian objectives on near-term devices; broad speedup is not guaranteed.",
        acceleration_focus="Hybrid chemistry/materials sessions where a quantum processor estimates Hamiltonian expectation values.",
        problem_tags=(
            "vqe",
            "chemistry",
            "ground_state",
            "hamiltonian",
            "materials",
            "eigenvalue",
            "hybrid",
        ),
        session_signals=(
            "ground state",
            "molecular energy",
            "hamiltonian expectation",
            "variational",
            "chemistry",
        ),
        constraints=(
            "Requires a Hamiltonian encoding and classical optimizer loop.",
            "May be limited by barren plateaus, noise, and measurement cost.",
            "Good for demos and research prototypes, not a guaranteed production speedup.",
        ),
        hardware_readiness="near_term_hybrid_demo",
        payload_hint="hamiltonian_plus_ansatz",
        migration_tools=("hybrid-vqe-loop", "hamiltonian-term-translator"),
        platform_ids=("local", "ibm_quantum", "aws_braket", "azure_quantum"),
        references=("https://www.nature.com/articles/ncomms5213",),
    ),
    AlgorithmProfile(
        id="qaoa",
        name="Quantum approximate optimization algorithm",
        family="hybrid_variational",
        speedup_type="heuristic_near_term",
        speedup_summary="QAOA maps combinatorial optimization to parameterized quantum circuits; broad practical speedup is not guaranteed.",
        acceleration_focus="QUBO, MaxCut, scheduling, routing, and constraint optimization sessions that can be encoded as cost Hamiltonians.",
        problem_tags=(
            "optimization",
            "qubo",
            "maxcut",
            "scheduling",
            "routing",
            "portfolio",
            "constraint_optimization",
        ),
        session_signals=(
            "qubo",
            "maxcut",
            "schedule",
            "routing",
            "portfolio optimization",
            "combinatorial optimization",
        ),
        constraints=(
            "Requires a cost Hamiltonian and mixer design.",
            "Usually needs a classical optimizer loop and many circuit evaluations.",
            "Current use should be framed as exploratory or heuristic.",
        ),
        hardware_readiness="near_term_hybrid_demo",
        payload_hint="cost_hamiltonian_problem_json",
        migration_tools=("qubo-to-qaoa-translator", "hybrid-qaoa-loop"),
        platform_ids=("local", "ibm_quantum", "aws_braket", "azure_quantum"),
        references=("https://arxiv.org/abs/1411.4028",),
    ),
    AlgorithmProfile(
        id="quantum_annealing",
        name="Quantum annealing and Ising/QUBO solvers",
        family="annealing",
        speedup_type="heuristic_hardware_acceleration",
        speedup_summary="Annealing hardware can explore Ising/QUBO landscapes directly, but general speedup is workload and hardware dependent.",
        acceleration_focus="Binary optimization sessions already expressible as QUBO or Ising models.",
        problem_tags=(
            "annealing",
            "ising",
            "qubo",
            "binary_optimization",
            "scheduling",
            "routing",
            "constraint_optimization",
        ),
        session_signals=(
            "ising",
            "qubo",
            "binary variables",
            "anneal",
            "constraint optimization",
        ),
        constraints=(
            "Requires QUBO/Ising formulation and embedding on target hardware.",
            "Hybrid solver behavior is provider-specific.",
            "Best treated as a candidate accelerator, not a guaranteed replacement.",
        ),
        hardware_readiness="specialized_hardware_available",
        payload_hint="qubo_or_ising_problem_json",
        migration_tools=("qubo-normalizer", "annealing-sampler-adapter"),
        platform_ids=("dwave_leap",),
        references=("https://docs.dwavequantum.com/en/latest/concepts/index.html",),
    ),
)


def get_algorithm_catalog() -> tuple[AlgorithmProfile, ...]:
    return ALGORITHM_CATALOG


def get_platform_targets() -> tuple[PlatformTarget, ...]:
    return PLATFORM_TARGETS


def find_algorithm(algorithm_id: str) -> AlgorithmProfile:
    for profile in ALGORITHM_CATALOG:
        if profile.id == algorithm_id:
            return profile
    raise KeyError(f"unknown algorithm: {algorithm_id}")
