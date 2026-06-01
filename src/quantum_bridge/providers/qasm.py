from __future__ import annotations

import bisect
import math
import random
import re
from dataclasses import dataclass


class QasmError(ValueError):
    pass


@dataclass(frozen=True)
class Operation:
    name: str
    args: tuple[int, ...]


@dataclass(frozen=True)
class ParsedCircuit:
    num_qubits: int
    num_clbits: int
    operations: tuple[Operation, ...]
    measurements: tuple[tuple[int, int], ...]


_REGISTER_RE = re.compile(r"^(qreg|creg)\s+([A-Za-z_][A-Za-z0-9_]*)\[(\d+)\]$")
_BIT_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\[(\d+)\]$")


def parse_openqasm2(source: str) -> ParsedCircuit:
    q_offsets: dict[str, int] = {}
    q_sizes: dict[str, int] = {}
    c_offsets: dict[str, int] = {}
    c_sizes: dict[str, int] = {}
    operations: list[Operation] = []
    measurements: list[tuple[int, int]] = []
    measured = False

    for statement in _statements(source):
        lower = statement.lower()
        if lower.startswith("openqasm ") or lower.startswith("include "):
            continue

        register_match = _REGISTER_RE.match(statement)
        if register_match:
            kind, name, size_text = register_match.groups()
            size = int(size_text)
            if size < 1:
                raise QasmError(f"{kind} '{name}' must have at least one bit")
            if kind == "qreg":
                q_offsets[name] = sum(q_sizes.values())
                q_sizes[name] = size
            else:
                c_offsets[name] = sum(c_sizes.values())
                c_sizes[name] = size
            continue

        if lower.startswith("barrier"):
            continue

        if lower.startswith("measure "):
            measured = True
            left, right = _parse_measure(statement)
            measurements.extend(_expand_measure(left, right, q_offsets, q_sizes, c_offsets, c_sizes))
            continue

        if measured:
            raise QasmError("gates after measurement are not supported by the local simulator")

        operation = _parse_gate(statement, q_offsets, q_sizes)
        operations.extend(operation)

    num_qubits = sum(q_sizes.values())
    num_clbits = sum(c_sizes.values())

    if num_qubits < 1:
        raise QasmError("circuit must declare at least one qreg")

    if not measurements:
        num_clbits = num_clbits or num_qubits
        measurements = [(index, index) for index in range(min(num_qubits, num_clbits))]
    elif num_clbits < 1:
        raise QasmError("measurements require a creg declaration")

    return ParsedCircuit(
        num_qubits=num_qubits,
        num_clbits=num_clbits,
        operations=tuple(operations),
        measurements=tuple(measurements),
    )


def simulate_counts(source: str, shots: int, seed: int | None = None, max_qubits: int = 16) -> tuple[dict[str, int], ParsedCircuit]:
    circuit = parse_openqasm2(source)
    if circuit.num_qubits > max_qubits:
        raise QasmError(
            f"local simulator supports up to {max_qubits} qubits; circuit requested {circuit.num_qubits}"
        )

    state = [0j] * (1 << circuit.num_qubits)
    state[0] = 1 + 0j

    for operation in circuit.operations:
        _apply_operation(state, circuit.num_qubits, operation)

    counts = _sample_counts(state, circuit, shots, random.Random(seed))
    return counts, circuit


def _statements(source: str) -> list[str]:
    no_comments = []
    for line in source.splitlines():
        no_comments.append(line.split("//", 1)[0])
    return [part.strip() for part in "\n".join(no_comments).split(";") if part.strip()]


def _parse_measure(statement: str) -> tuple[str, str]:
    match = re.match(r"^measure\s+(.+?)\s*->\s*(.+)$", statement, flags=re.IGNORECASE)
    if not match:
        raise QasmError(f"invalid measurement statement: {statement}")
    return match.group(1).strip(), match.group(2).strip()


def _expand_measure(
    left: str,
    right: str,
    q_offsets: dict[str, int],
    q_sizes: dict[str, int],
    c_offsets: dict[str, int],
    c_sizes: dict[str, int],
) -> list[tuple[int, int]]:
    if left in q_sizes and right in c_sizes:
        if q_sizes[left] != c_sizes[right]:
            raise QasmError("measure register sizes must match")
        return [
            (q_offsets[left] + index, c_offsets[right] + index)
            for index in range(q_sizes[left])
        ]

    return [(_resolve_bit(left, q_offsets, q_sizes), _resolve_bit(right, c_offsets, c_sizes))]


def _parse_gate(
    statement: str,
    q_offsets: dict[str, int],
    q_sizes: dict[str, int],
) -> list[Operation]:
    match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s+(.+)$", statement)
    if not match:
        raise QasmError(f"invalid gate statement: {statement}")

    name = match.group(1).lower()
    args = [arg.strip() for arg in match.group(2).split(",")]

    if name in {"h", "x", "y", "z", "s", "sdg", "t", "tdg", "id"}:
        if len(args) != 1:
            raise QasmError(f"gate '{name}' expects one target")
        return [Operation(name, (target,)) for target in _resolve_qubit_targets(args[0], q_offsets, q_sizes)]

    if name == "cx":
        if len(args) != 2:
            raise QasmError("gate 'cx' expects control and target")
        return [
            Operation(
                name,
                (
                    _resolve_bit(args[0], q_offsets, q_sizes),
                    _resolve_bit(args[1], q_offsets, q_sizes),
                ),
            )
        ]

    raise QasmError(f"unsupported gate '{name}'")


def _resolve_qubit_targets(
    token: str,
    offsets: dict[str, int],
    sizes: dict[str, int],
) -> list[int]:
    if token in sizes:
        return [offsets[token] + index for index in range(sizes[token])]
    return [_resolve_bit(token, offsets, sizes)]


def _resolve_bit(token: str, offsets: dict[str, int], sizes: dict[str, int]) -> int:
    match = _BIT_RE.match(token)
    if not match:
        raise QasmError(f"expected indexed bit, got '{token}'")

    name, index_text = match.groups()
    if name not in sizes:
        raise QasmError(f"unknown register '{name}'")

    index = int(index_text)
    if index >= sizes[name]:
        raise QasmError(f"register index out of range: {token}")

    return offsets[name] + index


def _apply_operation(state: list[complex], num_qubits: int, operation: Operation) -> None:
    if operation.name == "cx":
        _apply_cx(state, operation.args[0], operation.args[1])
        return

    target = operation.args[0]
    matrix = _single_qubit_matrix(operation.name)
    _apply_single_qubit(state, target, matrix)


def _single_qubit_matrix(name: str) -> tuple[complex, complex, complex, complex]:
    inv_sqrt_2 = 1 / math.sqrt(2)
    phase_t = complex(math.cos(math.pi / 4), math.sin(math.pi / 4))

    matrices: dict[str, tuple[complex, complex, complex, complex]] = {
        "h": (inv_sqrt_2, inv_sqrt_2, inv_sqrt_2, -inv_sqrt_2),
        "x": (0, 1, 1, 0),
        "y": (0, -1j, 1j, 0),
        "z": (1, 0, 0, -1),
        "s": (1, 0, 0, 1j),
        "sdg": (1, 0, 0, -1j),
        "t": (1, 0, 0, phase_t),
        "tdg": (1, 0, 0, phase_t.conjugate()),
        "id": (1, 0, 0, 1),
    }
    return matrices[name]


def _apply_single_qubit(
    state: list[complex],
    target: int,
    matrix: tuple[complex, complex, complex, complex],
) -> None:
    mask = 1 << target
    m00, m01, m10, m11 = matrix

    for index in range(len(state)):
        if index & mask:
            continue
        paired = index | mask
        amp0 = state[index]
        amp1 = state[paired]
        state[index] = m00 * amp0 + m01 * amp1
        state[paired] = m10 * amp0 + m11 * amp1


def _apply_cx(state: list[complex], control: int, target: int) -> None:
    if control == target:
        raise QasmError("cx control and target must be different")

    control_mask = 1 << control
    target_mask = 1 << target

    for index in range(len(state)):
        if not index & control_mask or index & target_mask:
            continue
        paired = index | target_mask
        state[index], state[paired] = state[paired], state[index]


def _sample_counts(
    state: list[complex],
    circuit: ParsedCircuit,
    shots: int,
    rng: random.Random,
) -> dict[str, int]:
    probabilities = [abs(amplitude) ** 2 for amplitude in state]
    total = sum(probabilities)
    if total <= 0:
        raise QasmError("state vector has zero probability")

    cumulative: list[float] = []
    running = 0.0
    for probability in probabilities:
        running += probability / total
        cumulative.append(running)
    cumulative[-1] = 1.0

    counts: dict[str, int] = {}
    for _ in range(shots):
        basis_state = bisect.bisect_left(cumulative, rng.random())
        bitstring = _classical_bitstring(basis_state, circuit)
        counts[bitstring] = counts.get(bitstring, 0) + 1
    return dict(sorted(counts.items()))


def _classical_bitstring(basis_state: int, circuit: ParsedCircuit) -> str:
    classical_bits = [0] * circuit.num_clbits
    for qubit_index, clbit_index in circuit.measurements:
        classical_bits[clbit_index] = (basis_state >> qubit_index) & 1
    return "".join(str(classical_bits[index]) for index in range(circuit.num_clbits - 1, -1, -1))
