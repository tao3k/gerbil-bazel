#!/usr/bin/env python3
"""Run structural Bazel build scenarios and emit one JSON v1 receipt."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence


SCHEMA = "gerbil-bazel.build-scenario-receipt.v1"
PROJECT_COMPILE_MNEMONIC = "GerbilProjectCompile"
DEFAULT_TARGET = "//tests/smoke:compile"
DEPENDENCY_FLAG = "--//tests/smoke:dependency_state=changed"
CONFIGURATION_FINGERPRINT = hashlib.sha1(
    b"gerbil-bazel.configuration-delta.v1"
).hexdigest()


@dataclass(frozen=True)
class Scenario:
    identifier: str
    intent: str
    build_flags: tuple[str, ...]
    expected_labels: frozenset[str]


SCENARIOS = (
    Scenario(
        identifier="project-cold",
        intent="Build the declared project in a fresh Bazel output root.",
        build_flags=(),
        expected_labels=frozenset(
            {
                "//tests/smoke:compile",
                "//tests/smoke:dependency_compile",
                "//tests/smoke:independent_compile",
            }
        ),
    ),
    Scenario(
        identifier="identical-rerun",
        intent="Repeat the exact build without changing inputs or configuration.",
        build_flags=(),
        expected_labels=frozenset(),
    ),
    Scenario(
        identifier="dependency-delta",
        intent="Change one declared dependency while preserving the independent branch.",
        build_flags=(DEPENDENCY_FLAG,),
        expected_labels=frozenset(
            {
                "//tests/smoke:compile",
                "//tests/smoke:dependency_compile",
            }
        ),
    ),
    Scenario(
        identifier="configuration-delta",
        intent="Change the native ABI identity consumed by every project action.",
        build_flags=(
            "--repo_env=GERBIL_NATIVE_ABI=" + CONFIGURATION_FINGERPRINT,
        ),
        expected_labels=frozenset(
            {
                "//tests/smoke:compile",
                "//tests/smoke:dependency_compile",
                "//tests/smoke:independent_compile",
            }
        ),
    ),
)


def available_cpu_count() -> int:
    affinity = getattr(os, "sched_getaffinity", None)
    if affinity is not None:
        try:
            return max(1, len(affinity(0)))
        except OSError:
            pass
    return max(1, os.cpu_count() or 1)


def resolve_executable(requested: str | None, candidates: Sequence[str]) -> str:
    if requested:
        resolved = shutil.which(requested)
        if resolved:
            return resolved
        requested_path = Path(requested).expanduser()
        if requested_path.is_file() and os.access(requested_path, os.X_OK):
            return str(requested_path.resolve())
        raise RuntimeError(f"executable is unavailable: {requested}")
    for candidate in candidates:
        resolved = shutil.which(candidate)
        if resolved:
            return resolved
    raise RuntimeError(
        "Bazel is unavailable; set BAZEL or pass --bazel with a Bazel/Bazelisk path"
    )


def command_version(command: Sequence[str]) -> str:
    completed = subprocess.run(
        command,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    if completed.returncode != 0:
        return "unavailable"
    return completed.stdout.strip()


def decode_json_stream(path: Path) -> list[dict[str, Any]]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    source = path.read_text(encoding="utf-8")
    decoder = json.JSONDecoder()
    offset = 0
    records: list[dict[str, Any]] = []
    while offset < len(source):
        while offset < len(source) and source[offset].isspace():
            offset += 1
        if offset >= len(source):
            break
        record, offset = decoder.raw_decode(source, offset)
        if not isinstance(record, dict):
            raise ValueError(f"execution log record is not an object: {path}")
        records.append(record)
    return records


def output_tail(output: str, line_count: int = 30) -> list[str]:
    lines = output.splitlines()
    return lines[-line_count:]


def remove_scenario_root(path: Path) -> None:
    """Remove Bazel output trees after restoring owner write permissions."""
    for root, directories, files in os.walk(path):
        root_path = Path(root)
        try:
            root_path.chmod(root_path.stat().st_mode | stat.S_IRWXU)
        except FileNotFoundError:
            continue
        for name in directories:
            directory = root_path / name
            if directory.is_symlink():
                continue
            try:
                directory.chmod(directory.stat().st_mode | stat.S_IRWXU)
            except FileNotFoundError:
                pass
        for name in files:
            file = root_path / name
            if file.is_symlink():
                continue
            try:
                file.chmod(file.stat().st_mode | stat.S_IRUSR | stat.S_IWUSR)
            except FileNotFoundError:
                pass
    shutil.rmtree(path)


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
        target,
        "--color=no",
        "--curses=no",
        "--disk_cache=",
        "--noshow_progress",
        "--remote_cache=",
        f"--execution_log_json_file={execution_log}",
        *scenario.build_flags,
    ]
    started_ns = time.monotonic_ns()
    completed = subprocess.run(
        command,
        check=False,
        cwd=workspace,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    elapsed_ms = (time.monotonic_ns() - started_ns) // 1_000_000
    records = decode_json_stream(execution_log)
    project_records = [
        record
        for record in records
        if record.get("mnemonic") == PROJECT_COMPILE_MNEMONIC
    ]
    executed_labels = sorted(
        {
            str(record.get("targetLabel", ""))
            for record in project_records
            if not record.get("cacheHit", False)
        }
        - {""}
    )
    cache_hit_labels = sorted(
        {
            str(record.get("targetLabel", ""))
            for record in project_records
            if record.get("cacheHit", False)
        }
        - {""}
    )
    expected_labels = sorted(scenario.expected_labels)
    assertions = [
        {
            "name": "bazel-command-succeeded",
            "passed": completed.returncode == 0,
        },
        {
            "name": "gerbil-project-compile-frontier",
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
            "gerbilProjectCompileRecordCount": len(project_records),
            "expectedExecutedLabels": expected_labels,
            "observedExecutedLabels": executed_labels,
            "observedCacheHitLabels": cache_hit_labels,
        },
        "assertions": assertions,
    }
    if status == "failed":
        receipt["outputTail"] = output_tail(completed.stdout)
    return receipt


def optimization_decision(scenarios: Iterable[dict[str, Any]]) -> dict[str, Any]:
    by_id = {scenario["id"]: scenario for scenario in scenarios}
    failed = [
        identifier
        for identifier, scenario in by_id.items()
        if scenario["status"] != "passed"
    ]
    if "project-cold" in failed:
        candidate = "project-build-foundation"
    elif "identical-rerun" in failed:
        candidate = "identical-action-cache-reuse"
    elif "dependency-delta" in failed:
        candidate = "project-dependency-invalidation"
    elif "configuration-delta" in failed:
        candidate = "toolchain-configuration-identity"
    elif failed:
        candidate = "scenario-specific-correctness"
    else:
        candidate = "upstream-source-provisioning"
    return {
        "status": "blocked" if failed else "ready",
        "optimizationCandidate": candidate,
        "failedScenarios": failed,
        "reason": (
            "Repair the first failing structural boundary before timing optimization."
            if failed
            else "Project cache reuse and invalidation frontiers are structurally correct; "
            "measure the exact upstream source bootstrap next."
        ),
    }


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--bazel",
        default=os.environ.get("BAZEL"),
        help="Bazel or Bazelisk executable; defaults to BAZEL, bazelisk, then bazel",
    )
    parser.add_argument(
        "--receipt",
        type=Path,
        default=Path(".ci/receipts/build-scenarios.json"),
        help="JSON receipt output path",
    )
    parser.add_argument("--target", default=DEFAULT_TARGET)
    parser.add_argument(
        "--keep-root",
        action="store_true",
        help="Preserve the isolated Bazel output root for diagnosis",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str]) -> int:
    args = parse_args(argv)
    workspace = Path(__file__).resolve().parents[2]
    bazel = resolve_executable(args.bazel, ("bazelisk", "bazel"))
    scenario_root = Path(tempfile.mkdtemp(prefix="gerbil-bazel-scenarios-"))
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
                "system": platform.system().lower(),
                "architecture": platform.machine().lower(),
                "availableLogicalCpuCount": available_cpu_count(),
            },
            "toolchain": {
                "bazel": bazel,
                "bazelVersion": command_version((bazel, "--version")),
                "gerbilVersion": command_version(("gxi", "--version")),
            },
            "isolation": {
                "freshOutputUserRoot": True,
                "sharedActionCachesEnabled": False,
                "rootPreserved": args.keep_root,
            },
            "scenarios": results,
            "decision": decision,
        }
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        temporary_receipt = args.receipt.with_suffix(args.receipt.suffix + ".tmp")
        temporary_receipt.write_text(
            json.dumps(receipt, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        temporary_receipt.replace(args.receipt)
        print(json.dumps(receipt, separators=(",", ":"), sort_keys=True))
        return 0 if receipt["status"] == "passed" else 1
    finally:
        shutdown = subprocess.run(
            [bazel, f"--output_user_root={output_user_root}", "shutdown"],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        if shutdown.returncode != 0:
            print(
                "warning: isolated Bazel server shutdown failed: "
                + "\n".join(output_tail(shutdown.stdout, 10)),
                file=sys.stderr,
            )
        if args.keep_root:
            print(f"preserved scenario root: {scenario_root}", file=sys.stderr)
        else:
            try:
                remove_scenario_root(scenario_root)
            except OSError as error:
                print(
                    f"warning: could not remove scenario root {scenario_root}: {error}",
                    file=sys.stderr,
                )


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
