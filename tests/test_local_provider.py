from __future__ import annotations

import unittest

from quantum_bridge import BridgeClient, JobStatus, ResourceSpec
from quantum_bridge.providers.qasm import parse_openqasm2


BELL_QASM = """
OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
creg c[2];
h q[0];
cx q[0], q[1];
measure q -> c;
"""


class LocalProviderTests(unittest.TestCase):
    def test_bell_counts_only_contain_correlated_states(self) -> None:
        result = BridgeClient().run_qasm(
            BELL_QASM,
            ResourceSpec(shots=200, metadata={"seed": 7}),
            persist=False,
        )

        self.assertEqual(result.status, JobStatus.COMPLETED)
        self.assertEqual(set(result.counts), {"00", "11"})
        self.assertEqual(sum(result.counts.values()), 200)

    def test_resource_spec_rejects_invalid_shots(self) -> None:
        with self.assertRaises(ValueError):
            ResourceSpec(shots=0)

    def test_measure_register_expands_to_each_bit(self) -> None:
        circuit = parse_openqasm2(BELL_QASM)

        self.assertEqual(circuit.num_qubits, 2)
        self.assertEqual(circuit.num_clbits, 2)
        self.assertEqual(circuit.measurements, ((0, 0), (1, 1)))

    def test_requested_qubits_must_cover_circuit(self) -> None:
        result = BridgeClient().run_qasm(
            BELL_QASM,
            ResourceSpec(qubits=1, shots=10, metadata={"seed": 3}),
            persist=False,
        )

        self.assertEqual(result.status, JobStatus.FAILED)
        self.assertIn("requires 2 qubits", result.error or "")


if __name__ == "__main__":
    unittest.main()
