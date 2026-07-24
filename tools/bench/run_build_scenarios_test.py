#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("run_build_scenarios.py")
SPEC = importlib.util.spec_from_file_location("run_build_scenarios", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class ExecutionLogTest(unittest.TestCase):
    def test_decodes_concatenated_json_records(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "execution.json"
            path.write_text('{"mnemonic":"A"}\n{"mnemonic":"B"}\n')
            self.assertEqual(
                [record["mnemonic"] for record in MODULE.decode_json_stream(path)],
                ["A", "B"],
            )

    def test_normalizes_canonical_repository_labels(self) -> None:
        self.assertEqual(
            MODULE.package_action_name(
                "@@+gerbil+root_package_with_dependency//:package_1"
            ),
            "package_1",
        )


class ScenarioContractTest(unittest.TestCase):
    def test_scenarios_describe_package_action_boundaries(self) -> None:
        self.assertEqual(
            [scenario.identifier for scenario in MODULE.SCENARIOS],
            [
                "package-cold",
                "identical-rerun",
                "ambient-environment-delta",
                "configuration-delta",
            ],
        )
        self.assertEqual(
            MODULE.SCENARIOS[0].expected_labels,
            frozenset({"package_0", "package_1"}),
        )
        self.assertEqual(MODULE.SCENARIOS[1].expected_labels, frozenset())

    def test_package_cold_failure_names_package_boundary(self) -> None:
        decision = MODULE.optimization_decision(
            [
                {"id": "package-cold", "status": "failed"},
                {"id": "identical-rerun", "status": "passed"},
            ]
        )
        self.assertEqual(decision["status"], "blocked")
        self.assertEqual(
            decision["optimizationCandidate"],
            "repair-package-closure-execution",
        )


if __name__ == "__main__":
    unittest.main()
