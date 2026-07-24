#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("run_cache_restoration_scenarios.py")
SPEC = importlib.util.spec_from_file_location(
    "run_cache_restoration_scenarios",
    MODULE_PATH,
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def package_record(label: str, *, cache_hit: bool = False) -> dict[str, object]:
    return {
        "mnemonic": MODULE.PACKAGE_BUILD_MNEMONIC,
        "targetLabel": f"@@+gerbil+cache_restoration_graph//:{label}",
        "cacheHit": cache_hit,
    }


class ArchiveTest(unittest.TestCase):
    def test_package_archive_is_byte_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            package = Path(root) / "cache-dependency"
            (package / "src").mkdir(parents=True)
            (package / "gerbil.pkg").write_text(
                "(package: example.invalid/cache-dependency)\n",
                encoding="utf-8",
            )
            (package / "src/value.ss").write_text(
                "(def value 'baseline)\n",
                encoding="utf-8",
            )
            first = Path(root) / "first.tar.gz"
            second = Path(root) / "second.tar.gz"
            first_sha = MODULE.write_deterministic_package_archive(package, first)
            second_sha = MODULE.write_deterministic_package_archive(package, second)
            self.assertEqual(first_sha, second_sha)
            self.assertEqual(first.read_bytes(), second.read_bytes())


class PackageGraphTest(unittest.TestCase):
    def test_maps_roles_from_package_identity_not_index(self) -> None:
        graph = {
            "packages": [
                {
                    "manifest": {"package": MODULE.DEPENDENCY_IDENTITY},
                    "target": "//:package_7",
                },
                {
                    "manifest": {"package": MODULE.ROOT_IDENTITY},
                    "target": "//:package_3",
                },
            ]
        }
        self.assertEqual(
            MODULE.graph_action_roles(graph),
            {"dependency": "package_7", "root": "package_3"},
        )


class ScenarioReceiptTest(unittest.TestCase):
    def test_restoration_requires_explicit_cache_hit_labels(self) -> None:
        observation = MODULE.BuildObservation(
            elapsed_ms=1,
            exit_code=0,
            records=(
                package_record("package_0", cache_hit=True),
                package_record("package_1", cache_hit=True),
            ),
            output="",
        )
        receipt = MODULE.scenario_receipt(
            identifier="baseline-restoration",
            intent="restore",
            observation=observation,
            expected_executed=set(),
            expected_cache_hits={"package_0", "package_1"},
        )
        self.assertEqual(receipt["status"], "passed")
        self.assertEqual(
            receipt["actions"]["observedCacheHitLabels"],
            ["package_0", "package_1"],
        )

    def test_dependency_failure_names_reverse_closure_owner(self) -> None:
        decision = MODULE.restoration_decision(
            [
                {"id": "baseline-seed", "status": "passed"},
                {"id": "root-source-delta", "status": "passed"},
                {"id": "dependency-source-delta", "status": "failed"},
                {"id": "baseline-restoration", "status": "failed"},
            ]
        )
        self.assertEqual(decision["status"], "blocked")
        self.assertEqual(
            decision["optimizationCandidate"],
            "repair-dependency-reverse-closure-invalidation",
        )


class EvidenceLinkTest(unittest.TestCase):
    def test_related_receipt_is_content_addressed(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            workspace = Path(root)
            path = workspace / "build-scenarios.json"
            path.write_text(
                json.dumps(
                    {
                        "schema": MODULE.BUILD_SCENARIO_SCHEMA,
                        "status": "passed",
                    }
                ),
                encoding="utf-8",
            )
            evidence = MODULE.related_build_scenario(path, workspace)
            self.assertEqual(evidence["path"], "build-scenarios.json")
            self.assertRegex(evidence["sha256"], r"^[0-9a-f]{64}$")


class SchemaOwnerTest(unittest.TestCase):
    def test_schema_owns_exact_scenario_set(self) -> None:
        schema_path = (
            Path(__file__).resolve().parents[2]
            / "schemas/gerbil-bazel.cache-restoration-receipt.v1.schema.json"
        )
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        self.assertEqual(
            schema["properties"]["schema"]["const"],
            MODULE.SCHEMA,
        )
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(
            schema["$defs"]["scenario"]["properties"]["id"]["enum"],
            [
                "baseline-seed",
                "root-source-delta",
                "dependency-source-delta",
                "baseline-restoration",
            ],
        )


if __name__ == "__main__":
    unittest.main()
