#!/usr/bin/env python3
"""Prove package delta invalidation and private action-cache restoration."""

from __future__ import annotations

import argparse
import gzip
import json
import os
import platform
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from build_evidence import (
    action_name,
    command_output,
    decode_json_stream,
    mnemonic_records,
    remove_tree,
    resolve_executable,
    sha256_bytes,
    sha256_file,
    write_json_atomic,
)


SCHEMA = "gerbil-bazel.cache-restoration-receipt.v1"
BUILD_SCENARIO_SCHEMA = "gerbil-bazel.build-scenario-receipt.v1"
PACKAGE_BUILD_MNEMONIC = "GerbilPackageBuild"
TARGET = "@cache_restoration_graph//:build"
GRAPH_TARGET = "@cache_restoration_graph//:package-graph.json"
ROOT_IDENTITY = "example.invalid/cache-restoration-root"
DEPENDENCY_IDENTITY = "example.invalid/cache-restoration-dependency"
DEPENDENCY_REFERENCE = DEPENDENCY_IDENTITY
BASELINE_REVISION = "baseline"
DELTA_REVISION = "dependency-delta"
ROOT_SOURCE = Path("tests/smoke/cache-restoration-root/src/main.ss")
ROOT_MANIFEST = Path("tests/smoke/cache-restoration-root/gerbil.pkg")
DEPENDENCY_ROOT = Path("tests/smoke/cache-restoration-dependency")
DEPENDENCY_SOURCE = DEPENDENCY_ROOT / "src/value.ss"


@dataclass(frozen=True)
class BuildObservation:
    elapsed_ms: int
    exit_code: int
    records: tuple[dict[str, Any], ...]
    output: str


def ignored_workspace_entries(_directory: str, names: list[str]) -> set[str]:
    ignored_names = {
        ".cache",
        ".ci",
        ".data",
        ".devenv",
        ".direnv",
        ".git",
        "result",
    }
    return {
        name
        for name in names
        if name in ignored_names or name.startswith("bazel-")
    }


def copy_workspace(source: Path, destination: Path) -> None:
    shutil.copytree(
        source,
        destination,
        symlinks=True,
        ignore=ignored_workspace_entries,
    )


def write_deterministic_package_archive(
    package_root: Path,
    archive_path: Path,
) -> str:
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    with archive_path.open("wb") as raw_output:
        with gzip.GzipFile(
            filename="",
            mode="wb",
            fileobj=raw_output,
            mtime=0,
        ) as compressed:
            with tarfile.open(
                fileobj=compressed,
                mode="w",
                format=tarfile.USTAR_FORMAT,
            ) as archive:
                paths = [package_root, *sorted(package_root.rglob("*"))]
                for path in paths:
                    relative = path.relative_to(package_root)
                    archive_name = Path(package_root.name) / relative
                    info = archive.gettarinfo(
                        str(path),
                        arcname=archive_name.as_posix(),
                    )
                    info.uid = 0
                    info.gid = 0
                    info.uname = ""
                    info.gname = ""
                    info.mtime = 0
                    info.mode = 0o755 if path.is_dir() else 0o644
                    if path.is_file():
                        with path.open("rb") as source:
                            archive.addfile(info, source)
                    else:
                        archive.addfile(info)
    return sha256_file(archive_path)


def cache_module_block(
    *,
    archive_path: Path,
    revision: str,
    sha256: str,
) -> str:
    values = {
        "manifest": "//tests/smoke:cache-restoration-root/gerbil.pkg",
        "name": "cache_restoration_graph",
        "package": DEPENDENCY_IDENTITY,
        "reference": DEPENDENCY_REFERENCE,
        "revision": revision,
        "sha256": sha256,
        "strip_prefix": DEPENDENCY_ROOT.name,
        "url": archive_path.resolve().as_uri(),
    }
    quoted = {key: json.dumps(value) for key, value in values.items()}
    return f"""

# Generated only inside the isolated cache-restoration workspace.
gerbil.package(
    name = {quoted["name"]},
    manifest = {quoted["manifest"]},
)
gerbil.dependency(
    graph = {quoted["name"]},
    package = {quoted["package"]},
    reference = {quoted["reference"]},
    revision = {quoted["revision"]},
    sha256 = {quoted["sha256"]},
    strip_prefix = {quoted["strip_prefix"]},
    urls = [{quoted["url"]}],
)
use_repo(gerbil, {quoted["name"]})
"""


def write_scenario_module(
    *,
    archive_path: Path,
    base_module: str,
    module_path: Path,
    revision: str,
    sha256: str,
) -> None:
    module_path.write_text(
        base_module
        + cache_module_block(
            archive_path=archive_path,
            revision=revision,
            sha256=sha256,
        ),
        encoding="utf-8",
    )


def root_manifest(revision: str) -> bytes:
    return (
        "(package: example.invalid/cache-restoration-root\n"
        f' depend: ("{DEPENDENCY_REFERENCE}@{revision}"))\n'
    ).encode()


def bazel_startup_prefix(
    *,
    bazel: str,
    output_user_root: Path,
) -> list[str]:
    return [
        bazel,
        f"--output_user_root={output_user_root}",
        "--max_idle_secs=15",
    ]


def bazel_cache_flags(
    *,
    private_action_cache: Path,
    repository_cache: Path,
) -> list[str]:
    return [
        f"--repository_cache={repository_cache}",
        f"--disk_cache={private_action_cache}",
        "--remote_cache=",
    ]


def refresh_module_lock(
    *,
    bazel: str,
    output_user_root: Path,
    private_action_cache: Path,
    repository_cache: Path,
    workspace: Path,
) -> None:
    command = [
        *bazel_startup_prefix(
            bazel=bazel,
            output_user_root=output_user_root,
        ),
        "mod",
        "deps",
        *bazel_cache_flags(
            private_action_cache=private_action_cache,
            repository_cache=repository_cache,
        ),
        "--config=lock_update",
    ]
    completed = subprocess.run(
        command,
        cwd=workspace,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            "isolated module lock refresh failed:\n"
            + "\n".join(completed.stdout.splitlines()[-80:])
        )


def run_build(
    *,
    bazel: str,
    execution_log: Path,
    output_user_root: Path,
    private_action_cache: Path,
    repository_cache: Path,
    workspace: Path,
) -> BuildObservation:
    command = [
        *bazel_startup_prefix(
            bazel=bazel,
            output_user_root=output_user_root,
        ),
        "build",
        *bazel_cache_flags(
            private_action_cache=private_action_cache,
            repository_cache=repository_cache,
        ),
        f"--execution_log_json_file={execution_log}",
        TARGET,
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
    return BuildObservation(
        elapsed_ms=(time.monotonic_ns() - started_ns) // 1_000_000,
        exit_code=completed.returncode,
        records=tuple(decode_json_stream(execution_log)),
        output=completed.stdout,
    )


def package_action_sets(
    observation: BuildObservation,
) -> tuple[list[str], list[str], int]:
    package_records = mnemonic_records(
        observation.records,
        PACKAGE_BUILD_MNEMONIC,
    )
    executed = sorted(
        {
            action_name(str(record.get("targetLabel", "")))
            for record in package_records
            if not record.get("cacheHit", False)
        }
    )
    cache_hits = sorted(
        {
            action_name(str(record.get("targetLabel", "")))
            for record in package_records
            if record.get("cacheHit", False)
        }
    )
    return executed, cache_hits, len(package_records)


def scenario_receipt(
    *,
    identifier: str,
    intent: str,
    observation: BuildObservation,
    expected_executed: set[str],
    expected_cache_hits: set[str],
) -> dict[str, Any]:
    executed, cache_hits, record_count = package_action_sets(observation)
    assertions = [
        {
            "name": "bazel-command-succeeded",
            "passed": observation.exit_code == 0,
        },
        {
            "name": "executed-package-frontier",
            "passed": executed == sorted(expected_executed),
        },
        {
            "name": "cache-restoration-frontier",
            "passed": cache_hits == sorted(expected_cache_hits),
        },
    ]
    status = "passed" if all(item["passed"] for item in assertions) else "failed"
    result: dict[str, Any] = {
        "id": identifier,
        "intent": intent,
        "status": status,
        "elapsedMs": observation.elapsed_ms,
        "exitCode": observation.exit_code,
        "actions": {
            "executionLogRecordCount": len(observation.records),
            "gerbilPackageBuildRecordCount": record_count,
            "expectedExecutedLabels": sorted(expected_executed),
            "observedExecutedLabels": executed,
            "expectedCacheHitLabels": sorted(expected_cache_hits),
            "observedCacheHitLabels": cache_hits,
        },
        "assertions": assertions,
    }
    if status == "failed":
        result["outputTail"] = observation.output.splitlines()[-80:]
    return result


def graph_action_roles(graph: dict[str, Any]) -> dict[str, str]:
    roles: dict[str, str] = {}
    for package in graph["packages"]:
        identity = str(package["manifest"]["package"])
        if identity == ROOT_IDENTITY:
            roles["root"] = action_name(str(package["target"]))
        elif identity == DEPENDENCY_IDENTITY:
            roles["dependency"] = action_name(str(package["target"]))
    if set(roles) != {"root", "dependency"}:
        raise RuntimeError(f"cache scenario graph roles are incomplete: {roles}")
    return roles


def graph_json_path(
    *,
    bazel: str,
    output_user_root: Path,
    private_action_cache: Path,
    repository_cache: Path,
    workspace: Path,
) -> Path:
    startup = bazel_startup_prefix(
        bazel=bazel,
        output_user_root=output_user_root,
    )
    cache_flags = bazel_cache_flags(
        private_action_cache=private_action_cache,
        repository_cache=repository_cache,
    )
    relative_path = command_output(
        [*startup, "cquery", *cache_flags, "--output=files", GRAPH_TARGET],
        workspace,
    )
    execution_root = command_output(
        [*startup, "info", *cache_flags, "execution_root"],
        workspace,
    )
    path = Path(execution_root) / relative_path
    if not path.is_file():
        raise RuntimeError(f"package graph JSON is unavailable: {path}")
    return path


def restoration_decision(
    scenarios: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    failed = [
        scenario["id"]
        for scenario in scenarios
        if scenario["status"] != "passed"
    ]
    candidates = {
        "baseline-seed": "repair-cache-seed-package-closure",
        "root-source-delta": "repair-root-source-invalidation",
        "dependency-source-delta": "repair-dependency-reverse-closure-invalidation",
        "baseline-restoration": "repair-private-action-cache-restoration",
    }
    candidate = (
        candidates.get(failed[0], "repair-cache-restoration-frontier")
        if failed
        else "admit-source-and-dependency-delta-benchmarking"
    )
    return {
        "status": "blocked" if failed else "ready",
        "optimizationCandidate": candidate,
        "failedScenarios": failed,
        "reason": (
            "Repair the first failing cache boundary before timing optimization."
            if failed
            else "Source and dependency invalidation plus cache restoration are structurally correct."
        ),
    }


def resolve_receipt_path(path: str, workspace: Path) -> Path:
    resolved = Path(path)
    return resolved if resolved.is_absolute() else workspace / resolved


def related_build_scenario(
    path: Path,
    workspace: Path,
) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if value.get("schema") != BUILD_SCENARIO_SCHEMA:
        raise RuntimeError(f"unexpected related build scenario schema: {path}")
    if value.get("status") != "passed":
        raise RuntimeError(f"related build scenario did not pass: {path}")
    try:
        display_path = path.relative_to(workspace).as_posix()
    except ValueError:
        display_path = str(path)
    return {
        "schema": BUILD_SCENARIO_SCHEMA,
        "path": display_path,
        "sha256": sha256_file(path),
        "status": "passed",
    }


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bazel", default=os.environ.get("BAZEL", "bazelisk"))
    parser.add_argument(
        "--build-scenario-receipt",
        default=".ci/receipts/build-scenarios.json",
    )
    parser.add_argument(
        "--receipt",
        default=".ci/receipts/cache-restoration.json",
    )
    parser.add_argument("--keep-root", action="store_true")
    return parser.parse_args(argv)


def shutdown(
    bazel: str,
    output_user_root: Path,
    workspace: Path,
) -> None:
    if not workspace.exists():
        return
    subprocess.run(
        [bazel, f"--output_user_root={output_user_root}", "shutdown"],
        cwd=workspace,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )


def main(argv: Sequence[str]) -> int:
    args = parse_args(argv)
    source_workspace = Path(__file__).resolve().parents[2]
    bazel = resolve_executable(args.bazel)
    scenario_root = Path(tempfile.mkdtemp(prefix="gerbil-cache-restoration-"))
    workspace = scenario_root / "workspace"
    output_seed = scenario_root / "bazel-output-seed"
    output_restore = scenario_root / "bazel-output-restore"
    repository_cache = scenario_root / "repository-cache"
    private_action_cache = scenario_root / "private-action-cache"
    artifacts = scenario_root / "artifacts"
    scenarios: list[dict[str, Any]] = []

    try:
        copy_workspace(source_workspace, workspace)
        module_path = workspace / "MODULE.bazel"
        base_module = module_path.read_text(encoding="utf-8")
        root_source_path = workspace / ROOT_SOURCE
        root_manifest_path = workspace / ROOT_MANIFEST
        dependency_root = workspace / DEPENDENCY_ROOT
        dependency_source_path = workspace / DEPENDENCY_SOURCE
        baseline_root_source = root_source_path.read_bytes()
        baseline_dependency_source = dependency_source_path.read_bytes()
        baseline_manifest = root_manifest(BASELINE_REVISION)
        if root_manifest_path.read_bytes() != baseline_manifest:
            raise RuntimeError("cache restoration root manifest baseline drifted")

        baseline_archive = artifacts / "cache-dependency-baseline.tar.gz"
        baseline_archive_sha256 = write_deterministic_package_archive(
            dependency_root,
            baseline_archive,
        )
        write_scenario_module(
            archive_path=baseline_archive,
            base_module=base_module,
            module_path=module_path,
            revision=BASELINE_REVISION,
            sha256=baseline_archive_sha256,
        )
        refresh_module_lock(
            bazel=bazel,
            output_user_root=output_seed,
            private_action_cache=private_action_cache,
            repository_cache=repository_cache,
            workspace=workspace,
        )

        baseline_observation = run_build(
            bazel=bazel,
            execution_log=artifacts / "baseline-seed.execution.json",
            output_user_root=output_seed,
            private_action_cache=private_action_cache,
            repository_cache=repository_cache,
            workspace=workspace,
        )
        graph = json.loads(
            graph_json_path(
                bazel=bazel,
                output_user_root=output_seed,
                private_action_cache=private_action_cache,
                repository_cache=repository_cache,
                workspace=workspace,
            ).read_text(encoding="utf-8")
        )
        roles = graph_action_roles(graph)
        all_labels = {roles["root"], roles["dependency"]}
        scenarios.append(
            scenario_receipt(
                identifier="baseline-seed",
                intent="The baseline package closure executes and seeds one private action cache.",
                observation=baseline_observation,
                expected_executed=all_labels,
                expected_cache_hits=set(),
            )
        )

        delta_root_source = baseline_root_source + b"\n;; root-source-delta\n"
        root_source_path.write_bytes(delta_root_source)
        scenarios.append(
            scenario_receipt(
                identifier="root-source-delta",
                intent="A root-only source edit invalidates the root package and preserves its dependency.",
                observation=run_build(
                    bazel=bazel,
                    execution_log=artifacts / "root-source-delta.execution.json",
                    output_user_root=output_seed,
                    private_action_cache=private_action_cache,
                    repository_cache=repository_cache,
                    workspace=workspace,
                ),
                expected_executed={roles["root"]},
                expected_cache_hits=set(),
            )
        )
        root_source_path.write_bytes(baseline_root_source)

        delta_dependency_source = (
            baseline_dependency_source + b"\n;; dependency-source-delta\n"
        )
        dependency_source_path.write_bytes(delta_dependency_source)
        delta_archive = artifacts / "cache-dependency-delta.tar.gz"
        delta_archive_sha256 = write_deterministic_package_archive(
            dependency_root,
            delta_archive,
        )
        dependency_source_path.write_bytes(baseline_dependency_source)
        root_manifest_path.write_bytes(root_manifest(DELTA_REVISION))
        write_scenario_module(
            archive_path=delta_archive,
            base_module=base_module,
            module_path=module_path,
            revision=DELTA_REVISION,
            sha256=delta_archive_sha256,
        )
        refresh_module_lock(
            bazel=bazel,
            output_user_root=output_seed,
            private_action_cache=private_action_cache,
            repository_cache=repository_cache,
            workspace=workspace,
        )
        scenarios.append(
            scenario_receipt(
                identifier="dependency-source-delta",
                intent="A dependency archive delta invalidates the dependency and its root reverse closure.",
                observation=run_build(
                    bazel=bazel,
                    execution_log=artifacts
                    / "dependency-source-delta.execution.json",
                    output_user_root=output_seed,
                    private_action_cache=private_action_cache,
                    repository_cache=repository_cache,
                    workspace=workspace,
                ),
                expected_executed=all_labels,
                expected_cache_hits=set(),
            )
        )

        shutdown(bazel, output_seed, workspace)
        root_manifest_path.write_bytes(baseline_manifest)
        write_scenario_module(
            archive_path=baseline_archive,
            base_module=base_module,
            module_path=module_path,
            revision=BASELINE_REVISION,
            sha256=baseline_archive_sha256,
        )
        refresh_module_lock(
            bazel=bazel,
            output_user_root=output_restore,
            private_action_cache=private_action_cache,
            repository_cache=repository_cache,
            workspace=workspace,
        )
        scenarios.append(
            scenario_receipt(
                identifier="baseline-restoration",
                intent="A fresh output root restores the complete baseline closure from the private action cache.",
                observation=run_build(
                    bazel=bazel,
                    execution_log=artifacts / "baseline-restoration.execution.json",
                    output_user_root=output_restore,
                    private_action_cache=private_action_cache,
                    repository_cache=repository_cache,
                    workspace=workspace,
                ),
                expected_executed=set(),
                expected_cache_hits=all_labels,
            )
        )

        decision = restoration_decision(scenarios)
        receipt = {
            "schema": SCHEMA,
            "status": "passed" if decision["status"] == "ready" else "failed",
            "relatedEvidence": related_build_scenario(
                resolve_receipt_path(
                    args.build_scenario_receipt,
                    source_workspace,
                ),
                source_workspace,
            ),
            "host": {
                "system": platform.system(),
                "architecture": platform.machine(),
                "availableLogicalCpuCount": os.cpu_count() or 1,
            },
            "isolation": {
                "workspaceCopy": True,
                "privateActionCache": True,
                "sharedActionCachesEnabled": False,
                "seedOutputUserRootFresh": True,
                "restoreOutputUserRootFresh": True,
                "rootPreserved": args.keep_root,
            },
            "packageGraph": {
                "target": TARGET,
                "rootIdentity": ROOT_IDENTITY,
                "rootActionLabel": roles["root"],
                "dependencyIdentity": DEPENDENCY_IDENTITY,
                "dependencyActionLabel": roles["dependency"],
            },
            "mutations": {
                "rootSource": {
                    "path": ROOT_SOURCE.as_posix(),
                    "baselineSha256": sha256_bytes(baseline_root_source),
                    "deltaSha256": sha256_bytes(delta_root_source),
                },
                "dependencyArchive": {
                    "reference": DEPENDENCY_REFERENCE,
                    "baselineRevision": BASELINE_REVISION,
                    "baselineSha256": baseline_archive_sha256,
                    "deltaRevision": DELTA_REVISION,
                    "deltaSha256": delta_archive_sha256,
                },
            },
            "scenarios": scenarios,
            "decision": decision,
        }
        receipt_path = resolve_receipt_path(args.receipt, source_workspace)
        write_json_atomic(receipt_path, receipt)
        print(json.dumps(receipt, sort_keys=True, separators=(",", ":")))
        return 0 if receipt["status"] == "passed" else 1
    finally:
        shutdown(bazel, output_seed, workspace)
        shutdown(bazel, output_restore, workspace)
        if args.keep_root:
            print(f"preserved cache scenario root: {scenario_root}", file=sys.stderr)
        else:
            remove_tree(scenario_root)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
