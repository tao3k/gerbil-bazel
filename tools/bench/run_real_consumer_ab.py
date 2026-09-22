#!/usr/bin/env python3
"""Run adjacent cold Gerbil consumer A/B builds in isolated local clones."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable, Sequence

import run_std_make_scheduler_scenarios as framework


SCHEMA = "gerbil-bazel.real-consumer-ab-receipt.v1"

NATIVE_JOB_END = re.compile(
    r"execute compile job \((?P<kind>compile-file|compile-batch) "
    r"(?P<subject>.*?)\) event=end status=(?P<status>\S+) "
    r"elapsedMs=(?P<elapsed_ms>\d+)"
)


def package_phase_metrics(result: framework.CommandResult) -> dict[str, Any]:
    """Extract package-facing bottlenecks without timing Gerbil bootstrap."""
    observations = framework.build_observations(result)

    def observation(phase: str, event: str) -> dict[str, Any] | None:
        return next(
            (
                item
                for item in observations
                if item.get("phase") == phase and item.get("event") == event
            ),
            None,
        )

    def reported_ms(item: dict[str, Any] | None) -> float | None:
        if item is None:
            return None
        if "elapsedMs" in item:
            return float(item["elapsedMs"])
        return float(item["elapsedNs"]) / 1_000_000

    graph_ready = reported_ms(observation("graph", "ready"))
    graph_end = reported_ms(observation("graph", "end"))
    drain_start = observation("native-drain", "start")
    drain_end = observation("native-drain", "end")
    native_drain_ms = (
        (int(drain_end["elapsedNs"]) - int(drain_start["elapsedNs"])) / 1_000_000
        if drain_start is not None and drain_end is not None
        else None
    )
    longest_native_jobs: list[dict[str, Any]] = []
    for event in result.events:
        match = NATIVE_JOB_END.search(str(event["line"]))
        if match is None:
            continue
        longest_native_jobs.append(
            {
                "kind": match.group("kind"),
                "subject": match.group("subject"),
                "status": match.group("status"),
                "elapsedMs": int(match.group("elapsed_ms")),
            }
        )
    longest_native_jobs.sort(key=lambda item: int(item["elapsedMs"]), reverse=True)
    # These are package-visible log boundaries, not claimed internal function
    # timings. In particular, main-to-object includes executable preparation.
    def first_event_ns(predicate: Callable[[str], bool]) -> int | None:
        return next(
            (
                int(event["elapsedNs"])
                for event in result.events
                if predicate(str(event["line"]))
            ),
            None,
        )

    main_ns = first_event_ns(lambda line: line.strip() == "... compile main")
    first_executable_object_ns = first_event_ns(
        lambda line: "execute compile job (compile-executable-object " in line
    )
    link_executable_ns = first_event_ns(
        lambda line: "execute compile job (link-executable " in line
    )

    def interval_ms(start_ns: int | None, end_ns: int | None) -> float | None:
        if start_ns is None or end_ns is None or end_ns < start_ns:
            return None
        return (end_ns - start_ns) / 1_000_000

    silence = framework.silence_observation(result)
    return {
        "graphReadyMs": graph_ready,
        "graphWorkMs": (
            graph_end - graph_ready
            if graph_ready is not None and graph_end is not None
            else None
        ),
        "graphTotalMs": graph_end,
        "nativeDrainMs": native_drain_ms,
        "frontendMs": reported_ms(observation("frontend", "end")),
        "buildStartToMainMs": interval_ms(0, main_ns),
        "mainToFirstExecutableObjectMs": interval_ms(
            main_ns, first_executable_object_ns
        ),
        "firstExecutableObjectToLinkMs": interval_ms(
            first_executable_object_ns, link_executable_ns
        ),
        "linkToBuildEndMs": interval_ms(link_executable_ns, result.elapsed_ns),
        "maxSilenceMs": int(silence.get("maxGapNs", 0)) / 1_000_000,
        "longestNativeJobs": longest_native_jobs[:8],
    }


def bottleneck_comparison(
    baseline: dict[str, Any], candidate: dict[str, Any]
) -> dict[str, Any]:
    metrics: dict[str, Any] = {}
    for name in (
        "graphReadyMs",
        "graphWorkMs",
        "graphTotalMs",
        "nativeDrainMs",
        "frontendMs",
        "buildStartToMainMs",
        "mainToFirstExecutableObjectMs",
        "firstExecutableObjectToLinkMs",
        "linkToBuildEndMs",
        "maxSilenceMs",
    ):
        baseline_value = baseline.get(name)
        candidate_value = candidate.get(name)
        if baseline_value is None or candidate_value is None:
            metrics[name] = {
                "baselineMs": baseline_value,
                "candidateMs": candidate_value,
                "deltaMs": None,
                "deltaPercent": None,
            }
            continue
        delta = float(candidate_value) - float(baseline_value)
        metrics[name] = {
            "baselineMs": baseline_value,
            "candidateMs": candidate_value,
            "deltaMs": delta,
            "deltaPercent": (
                delta / float(baseline_value) * 100 if baseline_value else None
            ),
        }
    return {
        "metrics": metrics,
        "baselineLongestNativeJobs": baseline.get("longestNativeJobs", []),
        "candidateLongestNativeJobs": candidate.get("longestNativeJobs", []),
    }


def performance_admission(
    baseline_ns: int,
    candidate_ns: int,
    *,
    max_regression_percent: float,
    max_candidate_seconds: float | None,
) -> dict[str, Any]:
    relative_limit_ns = baseline_ns * (1.0 + max_regression_percent / 100.0)
    relative_passed = candidate_ns <= relative_limit_ns
    absolute_passed = (
        max_candidate_seconds is None
        or candidate_ns <= max_candidate_seconds * 1_000_000_000
    )
    return {
        "maxRegressionPercent": max_regression_percent,
        "maxCandidateSeconds": max_candidate_seconds,
        "relativePassed": relative_passed,
        "absolutePassed": absolute_passed,
        "passed": relative_passed and absolute_passed,
    }


def measurement_timeout_seconds(
    label: str, build_timeout: float, candidate_timeout: float | None
) -> float:
    if label == "candidate" and candidate_timeout is not None:
        return min(build_timeout, candidate_timeout)
    return build_timeout


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require_binary_sha256(
    selected: dict[str, str], expected: str, *, label: str
) -> str:
    normalized_expected = expected.strip().lower()
    if len(normalized_expected) != 64 or any(
        character not in "0123456789abcdef" for character in normalized_expected
    ):
        raise RuntimeError(f"invalid {label} gerbil SHA256: {expected!r}")
    actual = sha256_file(Path(selected["gerbil"]))
    if actual != normalized_expected:
        raise RuntimeError(
            f"{label} gerbil identity mismatch: expected {normalized_expected}, "
            f"got {actual} at {selected['gerbil']}"
        )
    return actual


def write_qualification_failure(
    receipt_path: Path, *, consumer: str, phase: str, run: dict[str, Any]
) -> None:
    """Retain the exact watchdog/last-owner evidence when admission stops early."""
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(
        json.dumps(
            {
                "schema": SCHEMA,
                "status": "qualification-failed",
                "consumer": consumer,
                "failedPhase": phase,
                "run": run,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def git_output(repository: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ("git", "-C", str(repository), *arguments),
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return completed.stdout.strip()


def clone_repository(source: Path, destination: Path) -> None:
    subprocess.run(
        ("git", "clone", "--local", "--quiet", str(source), str(destination)),
        check=True,
    )


def warm_tracked_sources(repository: Path) -> dict[str, Any]:
    completed = subprocess.run(
        ("git", "-C", str(repository), "ls-files", "-z"),
        check=True,
        stdout=subprocess.PIPE,
    )
    digest = hashlib.sha256()
    file_count = 0
    byte_count = 0
    for encoded in completed.stdout.split(b"\0"):
        if not encoded:
            continue
        path = repository / os.fsdecode(encoded)
        if not path.is_file():
            continue
        payload = path.read_bytes()
        digest.update(encoded)
        digest.update(b"\0")
        digest.update(payload)
        file_count += 1
        byte_count += len(payload)
    return {
        "trackedFileCount": file_count,
        "trackedByteCount": byte_count,
        "contentSha256": digest.hexdigest(),
    }


def toolchain(home: Path) -> dict[str, str]:
    resolved_home = home.expanduser().resolve()
    gxi = framework.resolve_executable(
        str(resolved_home / "bin" / "gxi"), (), name="gxi"
    )
    gsc = framework.resolve_executable(
        str(resolved_home / "bin" / "gsc"), (), name="gsc"
    )
    checked_home = framework.resolve_toolchain_home(gxi, gsc, resolved_home)
    gxc = framework.resolve_executable(
        str(checked_home / "bin" / "gxc"), (), name="gxc"
    )
    gerbil = framework.resolve_executable(
        str(checked_home / "bin" / "gerbil"), (), name="gerbil"
    )
    return {
        "home": str(checked_home),
        "gxi": gxi,
        "gsc": gsc,
        "gxc": gxc,
        "gerbil": gerbil,
    }


def installed_library_identity(home: Path) -> dict[str, Any]:
    library = home / "lib"
    required = (
        "gerbil/compiler/base~0.o1",
        "gerbil/compiler/driver~0.o1",
        "std/make.o1",
        "static/gerbil__compiler__driver.scm",
    )
    return {
        "requestedRoot": str(library),
        "resolvedRoot": str(library.resolve()),
        "rootIsSymlink": library.is_symlink(),
        "requiredModuleSha256": {
            name: sha256_file(library / name) for name in required
        },
    }


def build_environment(
    selected: dict[str, str], repository: Path, build_cores: int, gcc: str | None
) -> dict[str, str]:
    environment = framework.sanitize_build_environment(os.environ)
    environment.pop("GERBIL_DARWIN_CANONICAL_RUNTIME_OBJECTS", None)
    tool_bin = str(Path(selected["home"]) / "bin")
    runtime_options = (
        f"~~={selected['home']},~~bin={tool_bin},"
        f"~~lib={Path(selected['home']) / 'lib'}"
    )
    environment.update(
        {
            "PATH": os.pathsep.join((tool_bin, environment.get("PATH", ""))),
            "GERBIL_HOME": selected["home"],
            "GERBIL_PATH": str(repository / ".gerbil"),
            "GERBIL_GSC": selected["gsc"],
            "GERBIL_GXC": selected["gxc"],
            "GERBIL_BUILD_CORES": str(build_cores),
            "GERBIL_BUILD_VERBOSE": "3",
            "GAMBOPT": ",".join(
                option
                for option in (environment.get("GAMBOPT", ""), runtime_options)
                if option
            ),
        }
    )
    if gcc is not None:
        environment["CC"] = gcc
        environment["GERBIL_GCC"] = gcc
    if selected.get("canonicalRuntimeObjects") == "yes":
        environment["GERBIL_DARWIN_CANONICAL_RUNTIME_OBJECTS"] = "yes"
    return environment


def build_command(
    consumer: str, repository: Path, selected: dict[str, str]
) -> tuple[str, ...]:
    if consumer == "gerbil-poo":
        just = framework.resolve_executable(None, ("just",), name="just")
        return (
            just,
            "--justfile",
            str(repository / "justfile"),
            "--working-directory",
            str(repository),
            "build",
        )
    make = framework.resolve_executable(None, ("make",), name="make")
    return (make, "build", f"GERBIL={selected['gerbil']}")


def qualify_toolchain_imports(
    *,
    label: str,
    consumer: str,
    repository: Path,
    selected: dict[str, str],
    build_cores: int,
    gcc: str | None,
) -> dict[str, Any]:
    """Bounded toolchain preflight; never build the cold consumer as warmup."""
    result = framework.run_timed(
        (
            selected["gxi"],
            "-e",
            "(import :std/make :std/encoding/json :std/net/ssl/libssl)",
            "-e",
            '(displayln "toolchain-imports-qualified")',
        ),
        phase=f"{consumer}-{label}-toolchain-imports",
        cwd=repository,
        environment=build_environment(selected, repository, build_cores, gcc),
        timeout_seconds=30.0,
        silence_timeout_seconds=30.0,
    )
    return {
        "mode": "toolchain-imports-only",
        "elapsedNs": result.elapsed_ns,
        "exitCode": result.exit_code,
        "timedOut": result.timed_out,
        "timeoutReason": result.timeout_reason,
        "events": list(result.events),
        "passed": result.exit_code == 0 and not result.timed_out,
    }


def clean_command(
    consumer: str, repository: Path, selected: dict[str, str]
) -> tuple[str, ...]:
    if consumer == "gerbil-poo":
        just = framework.resolve_executable(None, ("just",), name="just")
        return (
            just,
            "--justfile",
            str(repository / "justfile"),
            "--working-directory",
            str(repository),
            "clean",
        )
    make = framework.resolve_executable(None, ("make",), name="make")
    return (make, "clean", f"GERBIL={selected['gerbil']}")


def run_one(
    *,
    label: str,
    consumer: str,
    repository: Path,
    selected: dict[str, str],
    build_cores: int,
    gcc: str | None,
    timeout_seconds: float,
    silence_timeout_seconds: float,
) -> dict[str, Any]:
    revision_before = git_output(repository, "rev-parse", "HEAD")
    status_before = git_output(
        repository, "status", "--porcelain", "--untracked-files=no"
    )
    source_warmup = warm_tracked_sources(repository)
    environment = build_environment(selected, repository, build_cores, gcc)
    resolved_modules = {
        "compilerDriver": framework.probe_module_path(
            selected["gxi"], "gerbil/compiler/driver", environment
        ),
        "stdMake": framework.probe_module_path(selected["gxi"], "std/make", environment),
    }
    expected_root = str((Path(selected["home"]) / "lib").resolve())
    module_roots_match = all(
        str(Path(module).resolve()).startswith(expected_root + os.sep)
        for module in resolved_modules.values()
    )
    command = build_command(consumer, repository, selected)
    result = framework.run_timed(
        command,
        phase=f"{consumer}-{label}",
        cwd=repository,
        environment=environment,
        timeout_seconds=timeout_seconds,
        silence_timeout_seconds=silence_timeout_seconds,
        pseudo_terminal=True,
    )
    revision_after = git_output(repository, "rev-parse", "HEAD")
    status_after = git_output(
        repository, "status", "--porcelain", "--untracked-files=no"
    )
    executable = repository / ".gerbil" / "bin" / "gerbil-mcp"
    executable_identity = (
        framework.executable_identity(str(executable))
        if consumer == "gerbil-mcp" and executable.is_file()
        else None
    )
    assertions = {
        "sourceInitiallyClean": status_before == "",
        "sourceRevisionStable": revision_before == revision_after,
        "sourceRemainsClean": status_after == "",
        "moduleRootsMatchToolchain": module_roots_match,
        "buildSucceeded": result.exit_code == 0 and not result.timed_out,
        "consumerExecutableExists": consumer != "gerbil-mcp" or executable_identity is not None,
    }
    return {
        "label": label,
        "repository": str(repository),
        "revision": revision_before,
        "command": list(command),
        "toolchain": {
            **selected,
            "gxiExecutable": framework.executable_identity(selected["gxi"]),
            "gscExecutable": framework.executable_identity(selected["gsc"]),
            "installedLibrary": installed_library_identity(Path(selected["home"])),
            "resolvedModules": resolved_modules,
        },
        "elapsedNs": result.elapsed_ns,
        "exitCode": result.exit_code,
        "timedOut": result.timed_out,
        "timeoutReason": result.timeout_reason,
        "silence": framework.silence_observation(result),
        "packagePhaseMetrics": package_phase_metrics(result),
        "events": list(result.events),
        "sourceStatusAfter": status_after.splitlines(),
        "sourceWarmup": source_warmup,
        "consumerExecutable": executable_identity,
        "assertions": assertions,
        "passed": all(assertions.values()),
    }


def clear_consumer_outputs(repository: Path) -> None:
    output = repository / ".gerbil"
    if output.exists():
        shutil.rmtree(output)
    manifest = repository / "manifest.ss"
    if manifest.exists() and not git_output(repository, "ls-files", "manifest.ss"):
        manifest.unlink()


def prepare_measurement_state(
    *,
    build_state: str,
    consumer: str,
    repository: Path,
    selected: dict[str, str],
    build_cores: int,
    gcc: str | None,
    timeout_seconds: float,
) -> dict[str, Any]:
    if build_state == "cold":
        clear_consumer_outputs(repository)
        return {"mode": "cold", "command": None, "passed": True}
    if build_state != "native-warm":
        raise RuntimeError(f"unknown build state: {build_state}")
    command = clean_command(consumer, repository, selected)
    result = framework.run_timed(
        command,
        phase=f"{consumer}-prepare-native-warm",
        cwd=repository,
        environment=build_environment(selected, repository, build_cores, gcc),
        timeout_seconds=timeout_seconds,
        silence_timeout_seconds=10.0,
        pseudo_terminal=True,
    )
    return {
        "mode": "native-warm",
        "command": list(command),
        "elapsedNs": result.elapsed_ns,
        "exitCode": result.exit_code,
        "timedOut": result.timed_out,
        "passed": result.exit_code == 0 and not result.timed_out,
    }


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--consumer", choices=("gerbil-poo", "gerbil-mcp"), required=True)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--baseline-home", type=Path, required=True)
    parser.add_argument("--candidate-home", type=Path, required=True)
    parser.add_argument("--candidate-canonical-runtime-objects", action="store_true")
    parser.add_argument("--expected-baseline-gerbil-sha256", required=True)
    parser.add_argument("--expected-candidate-gerbil-sha256")
    parser.add_argument("--build-cores", type=int, default=framework.available_cpu_count())
    parser.add_argument("--gcc")
    parser.add_argument("--build-timeout", type=float, default=180.0)
    parser.add_argument("--candidate-timeout", type=float)
    parser.add_argument("--silence-timeout", type=float, default=10.0)
    parser.add_argument("--max-regression-percent", type=float, default=0.0)
    parser.add_argument("--max-candidate-seconds", type=float)
    parser.add_argument(
        "--build-state", choices=("cold", "native-warm"), default="cold"
    )
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--keep-root", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str]) -> int:
    args = parse_args(argv)
    if args.build_cores < 1:
        raise RuntimeError("--build-cores must be positive")
    if args.max_regression_percent < 0:
        raise RuntimeError("--max-regression-percent must not be negative")
    if args.max_candidate_seconds is not None and args.max_candidate_seconds <= 0:
        raise RuntimeError("--max-candidate-seconds must be positive")
    if args.candidate_timeout is not None and args.candidate_timeout <= 0:
        raise RuntimeError("--candidate-timeout must be positive")
    source = args.repository.expanduser().resolve()
    if git_output(source, "status", "--porcelain"):
        raise RuntimeError(f"source repository is dirty: {source}")
    gcc = args.gcc
    if gcc is None and platform.system() == "Darwin":
        gcc = framework.resolve_executable(None, ("gcc-16",), name="Darwin GCC")
    scenario_root = Path(tempfile.mkdtemp(prefix=f"{args.consumer}-ab-"))
    # First access is an explicit cache/toolchain qualification run, not a
    # measured package build.  Keep the 10 second hard silence gate on the
    # baseline/candidate measurements while allowing cold first access to
    # populate host caches without making that excluded run the benchmark.
    first_access_silence_timeout = (
        max(args.silence_timeout, 30.0)
        if args.build_state == "native-warm"
        else 10.0
    )
    try:
        repository = scenario_root / "consumer"
        clone_repository(source, repository)
        baseline_toolchain = toolchain(args.baseline_home)
        candidate_toolchain = toolchain(args.candidate_home)
        if args.candidate_canonical_runtime_objects:
            candidate_toolchain["canonicalRuntimeObjects"] = "yes"
        baseline_sha256 = require_binary_sha256(
            baseline_toolchain,
            args.expected_baseline_gerbil_sha256,
            label="baseline",
        )
        candidate_sha256 = sha256_file(Path(candidate_toolchain["gerbil"]))
        if args.expected_candidate_gerbil_sha256 is not None:
            candidate_sha256 = require_binary_sha256(
                candidate_toolchain,
                args.expected_candidate_gerbil_sha256,
                label="candidate",
            )
        if args.build_state == "native-warm":
            first_access = run_one(
                label="first-access-excluded",
                consumer=args.consumer,
                repository=repository,
                selected=baseline_toolchain,
                build_cores=args.build_cores,
                gcc=gcc,
                timeout_seconds=args.build_timeout,
                silence_timeout_seconds=first_access_silence_timeout,
            )
        else:
            first_access = qualify_toolchain_imports(
                label="baseline",
                consumer=args.consumer,
                repository=repository,
                selected=baseline_toolchain,
                build_cores=args.build_cores,
                gcc=gcc,
            )
        if not first_access["passed"]:
            write_qualification_failure(
                args.receipt,
                consumer=args.consumer,
                phase="baseline-first-access",
                run=first_access,
            )
            raise RuntimeError("first-access qualification failed")
        candidate_first_access = None
        if args.build_state == "cold":
            # Qualify both installed toolchains before either timed build.
            # A completed cold consumer build can otherwise put the host under
            # memory pressure and turn the second import into an order effect.
            candidate_first_access = qualify_toolchain_imports(
                label="candidate",
                consumer=args.consumer,
                repository=repository,
                selected=candidate_toolchain,
                build_cores=args.build_cores,
                gcc=gcc,
            )
            if not candidate_first_access["passed"]:
                write_qualification_failure(
                    args.receipt,
                    consumer=args.consumer,
                    phase="candidate-first-access",
                    run=candidate_first_access,
                )
                raise RuntimeError("candidate first-access qualification failed")
        baseline_preparation = prepare_measurement_state(
            build_state=args.build_state,
            consumer=args.consumer,
            repository=repository,
            selected=baseline_toolchain,
            build_cores=args.build_cores,
            gcc=gcc,
            timeout_seconds=args.build_timeout,
        )
        if not baseline_preparation["passed"]:
            raise RuntimeError("baseline measurement-state preparation failed")
        runs = []
        for label, selected in (
            ("baseline", baseline_toolchain),
            ("candidate", candidate_toolchain),
        ):
            candidate_preparation = None
            if label == "candidate":
                clear_consumer_outputs(repository)
                if args.build_state == "native-warm":
                    candidate_first_access = run_one(
                        label="candidate-first-access-excluded",
                        consumer=args.consumer,
                        repository=repository,
                        selected=selected,
                        build_cores=args.build_cores,
                        gcc=gcc,
                        timeout_seconds=args.build_timeout,
                        silence_timeout_seconds=first_access_silence_timeout,
                    )
                if not candidate_first_access["passed"]:
                    write_qualification_failure(
                        args.receipt,
                        consumer=args.consumer,
                        phase="candidate-first-access",
                        run=candidate_first_access,
                    )
                    raise RuntimeError("candidate first-access qualification failed")
                candidate_preparation = prepare_measurement_state(
                    build_state=args.build_state,
                    consumer=args.consumer,
                    repository=repository,
                    selected=selected,
                    build_cores=args.build_cores,
                    gcc=gcc,
                    timeout_seconds=args.build_timeout,
                )
                if not candidate_preparation["passed"]:
                    raise RuntimeError("candidate measurement-state preparation failed")
            run = run_one(
                label=label,
                consumer=args.consumer,
                repository=repository,
                selected=selected,
                build_cores=args.build_cores,
                gcc=gcc,
                timeout_seconds=measurement_timeout_seconds(
                    label, args.build_timeout, args.candidate_timeout
                ),
                silence_timeout_seconds=args.silence_timeout,
            )
            run["measurementState"] = args.build_state
            if label == "baseline":
                run["statePreparation"] = baseline_preparation
            elif candidate_preparation is not None:
                run["statePreparation"] = candidate_preparation
                run["firstAccessExcluded"] = candidate_first_access
            runs.append(run)
            if label == "baseline" and not run["passed"]:
                write_qualification_failure(
                    args.receipt,
                    consumer=args.consumer,
                    phase="baseline-measurement",
                    run=run,
                )
                raise RuntimeError("baseline measurement failed; candidate not comparable")
            if label == "baseline" and args.build_state == "cold":
                clear_consumer_outputs(repository)
        baseline_ns = runs[0]["elapsedNs"]
        candidate_ns = runs[1]["elapsedNs"]
        delta_ns = candidate_ns - baseline_ns
        admission = performance_admission(
            baseline_ns,
            candidate_ns,
            max_regression_percent=args.max_regression_percent,
            max_candidate_seconds=args.max_candidate_seconds,
        )
        receipt = {
            "schema": SCHEMA,
            "status": (
                "passed"
                if all(run["passed"] for run in runs) and admission["passed"]
                else "failed"
            ),
            "consumer": args.consumer,
            "host": {
                "system": platform.system().lower(),
                "architecture": platform.machine().lower(),
                "availableLogicalCpuCount": framework.available_cpu_count(),
            },
            "configuration": {
                "buildCores": args.build_cores,
                "gcc": gcc,
                "buildTimeoutSeconds": args.build_timeout,
                "candidateTimeoutSeconds": args.candidate_timeout,
                "silenceTimeoutSeconds": args.silence_timeout,
                "firstAccessSilenceTimeoutSeconds": first_access_silence_timeout,
                "buildState": args.build_state,
                "baselineGerbilSha256": baseline_sha256,
                "candidateGerbilSha256": candidate_sha256,
                "candidateCanonicalRuntimeObjects": args.candidate_canonical_runtime_objects,
                "maxRegressionPercent": args.max_regression_percent,
                "maxCandidateSeconds": args.max_candidate_seconds,
            },
            "runs": runs,
            "firstAccessExcluded": first_access,
            "comparison": {
                "baselineMs": baseline_ns / 1_000_000,
                "candidateMs": candidate_ns / 1_000_000,
                "deltaMs": delta_ns / 1_000_000,
                "deltaPercent": (100.0 * delta_ns / baseline_ns) if baseline_ns else None,
            },
            "admission": admission,
            "bottleneckComparison": bottleneck_comparison(
                runs[0]["packagePhaseMetrics"], runs[1]["packagePhaseMetrics"]
            ),
        }
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(
            json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        print(
            json.dumps(
                {
                    "status": receipt["status"],
                    "consumer": args.consumer,
                    **receipt["comparison"],
                    "receipt": str(args.receipt),
                },
                separators=(",", ":"),
                sort_keys=True,
            )
        )
        return 0 if receipt["status"] == "passed" else 1
    finally:
        if args.keep_root:
            print(f"preserved scenario root: {scenario_root}", file=sys.stderr)
        else:
            shutil.rmtree(scenario_root)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
