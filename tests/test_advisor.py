from __future__ import annotations

import unittest

from quantum_bridge.advisor import DEMO_SESSIONS, advise_sessions, algorithm_catalog_payload


class AdvisorTests(unittest.TestCase):
    def test_catalog_exposes_speedup_focus(self) -> None:
        payload = algorithm_catalog_payload()
        algorithms = {item["id"]: item for item in payload["algorithms"]}

        self.assertIn("grover_search", algorithms)
        self.assertIn("amplitude_estimation", algorithms)
        self.assertIn("acceleration_focus", algorithms["grover_search"])
        self.assertTrue(algorithms["grover_search"]["references"])

    def test_demo_sessions_return_migration_candidates(self) -> None:
        result = advise_sessions(DEMO_SESSIONS, preferred_platform="ibm_quantum")

        self.assertTrue(result["demo"])
        self.assertEqual(result["summary"]["sessions_received"], 3)
        self.assertEqual(result["summary"]["sessions_with_candidates"], 3)

    def test_monte_carlo_maps_to_amplitude_estimation(self) -> None:
        result = advise_sessions(
            [
                {
                    "session_id": "pricing",
                    "operation": "Monte Carlo expected value over many sample paths.",
                    "tags": ["monte_carlo", "expectation"],
                    "workload_size": 1000000,
                }
            ]
        )

        top = result["recommendations"][0]["candidates"][0]
        self.assertEqual(top["algorithm"]["id"], "amplitude_estimation")
        self.assertEqual(top["migration_tool"], "sampler-estimator-wrapper")

    def test_optimization_maps_to_qaoa_or_annealing(self) -> None:
        result = advise_sessions(
            [
                {
                    "session_id": "schedule",
                    "operation": "QUBO scheduling with binary variables.",
                    "tags": ["qubo", "scheduling", "optimization"],
                    "workload_size": 20000,
                }
            ]
        )

        algorithm_ids = [
            candidate["algorithm"]["id"]
            for candidate in result["recommendations"][0]["candidates"]
        ]
        self.assertIn("qaoa", algorithm_ids)

    def test_auth_request_mentions_cloud_credentials(self) -> None:
        result = advise_sessions(DEMO_SESSIONS, preferred_platform="ibm_quantum")
        platform_ids = {request["platform_id"] for request in result["auth_requests"]}

        self.assertIn("ibm_quantum", platform_ids)


if __name__ == "__main__":
    unittest.main()
