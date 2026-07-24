#!/usr/bin/env python3
"""Produce structural cache evidence for generated Gerbil package actions."""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence


SCHEMA = "gerbil-bazel.build-scenario-receipt.v1"
PACKAGE_BUILD_MNEMONIC = "GerbilPackageBuild"
DEFAULT_TARGET = "@root_package_with_dependency//:build"
EXPECTED_PACKAGE_ACTIONS = frozenset({"package_0", "package_1"})


@dataclass(frozen=True)
class Scenario:
    identifier: str
    intent: str
    build_flags: tuple[str, ...]
    expected_labels: frozenset[str]


SCENARIOS = (
    Scenario(
        "package-cold",
        "A fresh output root executes the complete reachable package closure.",
        (),
        EXPECTED_PACKAGE_ACTIONS,
    ),
    Scenario(
        "identical-rerun",
        "An identical graph and configuration execute no package action.",
        (),
        frozenset(),
    ),
    Scenario(
        "ambient-environment-delta",
        "An ambient Bazel action_env change cannot alter explicit package actions.",
        ("--action_env=GERBIL_BAZEL_SCENARIO_REVISION=1",),
        frozenset(),
    ),
    Scenario(
        "configuration-delta",
        "A Bazel compilation-mode change creates a distinct package action graph.",
        ("--compilation_mode=opt",),
        EXPECTED_PACKAGE_ACTIONS,
    ),
)


def resolve_executable(value: str) -> str:
    resolved = shutil.which(value)
    if resolved is None:
        raise RuntimeError(f"required executable is unavailable: {value}")
    return resolved


def decode_json_stream(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    decoder = json.JSONDecoder()
    records: list[dict[str, Any]] = []
    offset = 0
    while offset < len(text):
        while offset < len(text) and text[offset].isspace():
            offset += 1
        if offset == len(text):
            break
        value, offset = decoder.raw_decode(text, offset)
        if isinstance(value, dict):
            records.append(value)
        elif isinstance(value, list):
            records.extend(item for item in value if isinstance(item, dict))
    return records


def package_action_name(label: str) -> str:
    if "//:" not in label:
        return label
    return label.rsplit("//:", 1)[1]


def package_action_records(
    records: Iterable[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        record
        for record in records
        if record.get("mnemonic") == PACKAGE_BUILD_MNEMONIC
    ]


def action_label(record: dict[str, Any]) -> str:
    return package_action_name(str(record.get("targetLabel", "")))


def run_scenario(
    *,
    bazel: str,
    output_user_root: Path,
    scenario_root: Path,
    scenario: Scenario,
    target: str,
    workspace: Path,
) -> dict[str, Any]:
    execution_log = scenario_root / f"{scenario.identifier}.execution.json"
    command = [
        bazel,
        f"--output_user_root={output_user_root}",
        "build",
        "--disk_cache=",
        f"--repository_cache={scenario_root / 'repository-cache'}",
        f"--execution_log_json_file={execution_log}",
        *scenario.build_flags,
        target,
    ]
    started_ns = time.monotonic_ns()
    completed = subprocess.run(
        command,
        cwd=workspace,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    elapsed_ms = (time.monotonic_ns() - started_ns) // 1_000_000
    records = decode_json_stream(execution_log)
    package_records = package_action_records(records)
    executed_labels = sorted(
        {
            action_label(record)
            for record in package_records
            if not record.get("cacheHit", False)
        }
    )
    cache_hit_labels = sorted(
        {
            action_label(record)
            for record in package_records
            if record.get("cacheHit", False)
        }
    )
    expected_labels = sorted(scenario.expected_labels)
    assertions = [
        {
            "name": "bazel-command-succeeded",
            "passed": completed.returncode == 0,
        },
        {
            "name": "gerbil-package-build-frontier",
            "passed": executed_labels == expected_labels,
        },
    ]
    status = "passed" if all(item["passed"] for item in assertions) else "failed"
    receipt: dict[str, Any] = {
        "id": scenario.identifier,
        "intent": scenario.intent,
        "status": status,
        "elapsedMs": elapsed_ms,
        "exitCode": completed.returncode,
        "configuration": {
            "target": target,
            "buildFlags": list(scenario.build_flags),
        },
        "actions": {
            "executionLogRecordCount": len(records),
            "gerbilPackageBuildRecordCount": len(package_records),
            "expectedExecutedLabels": expected_labels,
            "observedExecutedLabels": executed_labels,
            "observedCacheHitLabels": cache_hit_labels,
        },
        "assertions": assertions,
    }
    if status == "failed":
        receipt["outputTail"] = completed.stdout.splitlines()[-80:]
    return receipt


def optimization_decision(
    scenarios: Iterable[dict[str, Any]],
) -> dict[str, Any]:
    failed = [
        scenario["id"]
        for scenario in scenarios
        if scenario["status"] != "passed"
    ]
    if "package-cold" in failed:
        candidate = "repair-package-closure-execution"
    elif "identical-rerun" in failed:
        candidate = "repair-identical-package-action-reuse"
    elif "ambient-environment-delta" in failed:
        candidate = "repair-ambient-environment-isolation"
    elif "configuration-delta" in failed:
        candidate = "repair-configuration-invalidation"
    elif failed:
        candidate = "repair-structural-package-frontier"
    else:
        candidate = "measure-package-action-duration"
    return {
        "status": "blocked" if failed else "ready",
        "optimizationCandidate": candidate,
        "failedScenarios": failed,
        "reason": (
            "Repair the first failing structural package boundary before timing "
            "optimization."
            if failed
            else "All package action frontiers are correct; timing work is admissible."
        ),
    }


def command_output(command: Sequence[str], workspace: Path) -> str:
    completed = subprocess.run(
        command,
        cwd=workspace,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    output = completed.stdout.strip()
    if completed.returncode != 0:
        diagnostic = completed.stderr.strip() or output
        raise RuntimeError(f"command failed ({completed.returncode}): {diagnostic}")
    if not output:
        raise RuntimeError(f"command produced no output: {' '.join(command)}")
    return output.splitlines()[-1]


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bazel", default=os.environ.get("BAZEL", "bazelisk"))
    parser.add_argument(
        "--receipt",
        default=".ci/receipts/build-scenarios.json",
    )
    parser.add_argument("--target", default=DEFAULT_TARGET)
    parser.add_argument("--keep-root", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str]) -> int:
    args = parse_args(argv)
    workspace = Path(__file__).resolve().parents[2]
    bazel = resolve_executable(args.bazel)
    scenario_root = Path(tempfile.mkdtemp(prefix="gerbil-package-scenarios-"))
    output_user_root = scenario_root / "bazel-output-user-root"
    results: list[dict[str, Any]] = []
    try:
        for scenario in SCENARIOS:
            results.append(
                run_scenario(
                    bazel=bazel,
                    output_user_root=output_user_root,
                    scenario_root=scenario_root,
                    scenario=scenario,
                    target=args.target,
                    workspace=workspace,
                )
            )
        decision = optimization_decision(results)
        receipt = {
            "schema": SCHEMA,
            "status": "passed" if decision["status"] == "ready" else "failed",
            "host": {
                "system": platform.system(),
                "architecture": platform.machine(),
                "availableLogicalCpuCount": os.cpu_count() or 1,
            },
            "toolchain": {
                "bazel": bazel,
                "bazelVersion": command_output([bazel, "--version"], workspace),
                "gerbilVersion": command_output(
                    [
                        bazel,
                        f"--output_user_root={output_user_root}",
                        "run",
                        "@local_gerbil//:gxi",
                        "--",
                        "--version",
                    ],
                    workspace,
                ),
            },
            "isolation": {
                "freshOutputUserRoot": True,
                "sharedActionCachesEnabled": False,
                "rootPreserved": args.keep_root,
            },
            "scenarios": results,
            "decision": decision,
        }
        receipt_path = Path(args.receipt)
        if not receipt_path.is_absolute():
            receipt_path = workspace / receipt_path
        receipt_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = receipt_path.with_suffix(receipt_path.suffix + ".tmp")
        temporary.write_text(
            json.dumps(receipt, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
        temporary.replace(receipt_path)
        print(json.dumps(receipt, sort_keys=True, separators=(",", ":")))
        return 0 if receipt["status"] == "passed" else 1
    finally:
        subprocess.run(
            [bazel, f"--output_user_root={output_user_root}", "shutdown"],
            cwd=workspace,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        if args.keep_root:
            print(f"preserved scenario root: {scenario_root}", file=sys.stderr)
        else:
            shutil.rmtree(scenario_root, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
