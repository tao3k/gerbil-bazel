#!/usr/bin/env python3
"""Measure the upstream Gerbil std/make scheduler with a neutral fixture."""

from __future__ import annotations

import argparse
import errno
import hashlib
import json
import os
import platform
import pty
import re
import selectors
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence


SCHEMA = "gerbil-bazel.std-make-scheduler-receipt.v1"


@dataclass(frozen=True)
class CommandResult:
    exit_code: int
    elapsed_ns: int
    timed_out: bool
    events: tuple[dict[str, Any], ...]
    timeout_reason: str | None = None

    @property
    def output(self) -> str:
        return "\n".join(str(event["line"]) for event in self.events)


def available_cpu_count() -> int:
    affinity = getattr(os, "sched_getaffinity", None)
    if affinity is not None:
        try:
            return max(1, len(affinity(0)))
        except OSError:
            pass
    return max(1, os.cpu_count() or 1)


def resolve_executable(
    requested: str | None, candidates: Sequence[str], *, name: str
) -> str:
    if requested:
        resolved = shutil.which(requested)
        if resolved:
            return resolved
        path = Path(requested).expanduser()
        if path.is_file() and os.access(path, os.X_OK):
            return str(path.resolve())
        raise RuntimeError(f"{name} executable is unavailable: {requested}")
    for candidate in candidates:
        resolved = shutil.which(candidate)
        if resolved:
            return resolved
    raise RuntimeError(f"{name} is unavailable")


def resolve_gerbil_gsc(gxi: str, requested: str | None) -> str:
    if requested:
        return resolve_executable(requested, (), name="gsc")
    completed = subprocess.run(
        [
            gxi,
            "-e",
            '(begin (displayln (path-expand "~~bin/gsc")) (exit 0))',
        ],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise RuntimeError(f"cannot resolve Gerbil's Gambit gsc: {detail}")
    return resolve_executable(completed.stdout.strip(), (), name="Gerbil Gambit gsc")


def resolve_toolchain_home(gxi: str, gsc: str, requested: Path | None) -> Path:
    home = (
        requested.expanduser().resolve()
        if requested is not None
        else Path(gxi).resolve().parent.parent
    )
    expected_bin = (home / "bin").resolve()
    for name, executable in (("gxi", gxi), ("gsc", gsc)):
        if Path(executable).resolve().parent != expected_bin:
            raise RuntimeError(
                f"cross-toolchain {name} rejected: {executable} is not under {expected_bin}"
            )
    resolve_executable(str(expected_bin / "gxc"), (), name="gxc")
    return home


def sanitize_build_environment(environment: dict[str, str]) -> dict[str, str]:
    result = environment.copy()
    if platform.system() == "Darwin":
        for name in (
            "SDKROOT",
            "DEVELOPER_DIR",
            "CPATH",
            "LIBRARY_PATH",
            "C_INCLUDE_PATH",
            "CPLUS_INCLUDE_PATH",
            "MACOSX_DEPLOYMENT_TARGET",
            "DYLD_LIBRARY_PATH",
            "DYLD_FALLBACK_LIBRARY_PATH",
        ):
            result.pop(name, None)
        result.setdefault("COMPILER_PATH", "/usr/bin")
    result.pop("GERBIL_LOADPATH", None)
    return result


def terminate_process_group(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        process.wait(timeout=0.5)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        process.wait()


def should_stream_line(line: str) -> bool:
    """Keep the terminal diagnostic; retain every raw line only in the receipt."""
    return (
        "... build-observe " in line
        or "... consumer-observe " in line
        or line.startswith("*** ERROR")
        or line.startswith("*** WARNING")
        or line.startswith("--- Syntax Error")
    )


def run_timed(
    command: Sequence[str],
    *,
    phase: str,
    cwd: Path,
    environment: dict[str, str],
    timeout_seconds: float,
    silence_timeout_seconds: float = 10.0,
    pseudo_terminal: bool = False,
) -> CommandResult:
    print(f"[std-make-scheduler] phase={phase} status=started", file=sys.stderr, flush=True)
    started_ns = time.monotonic_ns()
    last_output_ns = started_ns
    master_fd: int | None = None
    slave_fd: int | None = None
    if pseudo_terminal:
        master_fd, slave_fd = pty.openpty()
    process = subprocess.Popen(
        command,
        cwd=cwd,
        env=environment,
        stdout=slave_fd if slave_fd is not None else subprocess.PIPE,
        stderr=slave_fd if slave_fd is not None else subprocess.STDOUT,
        start_new_session=True,
    )
    if slave_fd is not None:
        os.close(slave_fd)
    output = master_fd if master_fd is not None else process.stdout
    assert output is not None
    selector = selectors.DefaultSelector()
    selector.register(output, selectors.EVENT_READ)
    pending = b""
    events: list[dict[str, Any]] = []
    timed_out = False
    timeout_reason: str | None = None
    try:
        while True:
            elapsed_seconds = (time.monotonic_ns() - started_ns) / 1_000_000_000
            if elapsed_seconds >= timeout_seconds:
                timed_out = True
                timeout_reason = "total"
                print(
                    f"[std-make-scheduler] phase={phase} status=timeout reason=total",
                    file=sys.stderr,
                    flush=True,
                )
                terminate_process_group(process)
                break
            silent_seconds = (time.monotonic_ns() - last_output_ns) / 1_000_000_000
            if silent_seconds >= silence_timeout_seconds:
                timed_out = True
                timeout_reason = "silence"
                print(
                    f"[std-make-scheduler] phase={phase} status=timeout reason=silence",
                    file=sys.stderr,
                    flush=True,
                )
                terminate_process_group(process)
                break
            ready = selector.select(timeout=min(0.1, timeout_seconds - elapsed_seconds))
            for key, _ in ready:
                try:
                    chunk = os.read(key.fd, 65536)
                except OSError as error:
                    if pseudo_terminal and error.errno == errno.EIO:
                        chunk = b""
                    else:
                        raise
                if not chunk:
                    selector.unregister(output)
                    continue
                last_output_ns = time.monotonic_ns()
                pending += chunk
                while b"\n" in pending:
                    raw, pending = pending.split(b"\n", 1)
                    line = raw.decode("utf-8", errors="replace").rstrip("\r")
                    events.append(
                        {
                            "elapsedNs": time.monotonic_ns() - started_ns,
                            "line": line,
                        }
                    )
                    if should_stream_line(line):
                        print(
                            f"[std-make-scheduler] phase={phase} {line}",
                            file=sys.stderr,
                            flush=True,
                        )
            if process.poll() is not None and not selector.get_map():
                break
        if pending:
            events.append(
                {
                    "elapsedNs": time.monotonic_ns() - started_ns,
                    "line": pending.decode("utf-8", errors="replace"),
                }
            )
    finally:
        selector.close()
        terminate_process_group(process)
        if process.stdout is not None:
            process.stdout.close()
        if master_fd is not None:
            os.close(master_fd)
    result = CommandResult(
        exit_code=process.returncode if process.returncode is not None else -1,
        elapsed_ns=time.monotonic_ns() - started_ns,
        timed_out=timed_out,
        events=tuple(events),
        timeout_reason=timeout_reason,
    )
    print(
        f"[std-make-scheduler] phase={phase} status=finished "
        f"exit={result.exit_code} timeout={str(result.timed_out).lower()} "
        f"elapsedNs={result.elapsed_ns}",
        file=sys.stderr,
        flush=True,
    )
    return result


def silence_observation(result: CommandResult) -> dict[str, Any]:
    """Attribute the largest event-free interval to its surrounding events."""
    boundaries: list[tuple[int, str]] = [(0, "<process-start>")]
    boundaries.extend(
        (int(event["elapsedNs"]), str(event["line"])) for event in result.events
    )
    terminal = (
        f"<watchdog:{result.timeout_reason}>"
        if result.timed_out
        else "<process-exit>"
    )
    boundaries.append((result.elapsed_ns, terminal))
    before, after = max(
        zip(boundaries, boundaries[1:]),
        key=lambda pair: pair[1][0] - pair[0][0],
    )
    return {
        "maxGapNs": after[0] - before[0],
        "beforeElapsedNs": before[0],
        "beforeEvent": before[1],
        "afterElapsedNs": after[0],
        "afterEvent": after[1],
        "timeoutReason": result.timeout_reason,
    }


def write_fixture(
    source_root: Path, independent_modules: int = 6, chain_modules: int = 3
) -> None:
    source_root.mkdir(parents=True, exist_ok=True)
    (source_root / "gerbil.pkg").write_text(
        "(package: std-make-scheduler-fixture)\n", encoding="utf-8"
    )
    (source_root / "upstream.ss").write_text(
        "(export value)\n(def value 41)\n", encoding="utf-8"
    )
    (source_root / "middle.ss").write_text(
        "(import ./upstream)\n(export middle-value)\n"
        "(def middle-value (+ value 1))\n",
        encoding="utf-8",
    )
    (source_root / "leaf.ss").write_text(
        "(import ./middle)\n(export answer)\n(def answer middle-value)\n",
        encoding="utf-8",
    )
    previous_module = "leaf"
    previous_binding = "answer"
    extra_chain_modules: list[str] = []
    for index in range(3, chain_modules):
        module = f"chain-{index}"
        binding = f"chain-value-{index}"
        (source_root / f"{module}.ss").write_text(
            f"(import ./{previous_module})\n(export {binding})\n"
            f"(def {binding} (+ {previous_binding} 1))\n",
            encoding="utf-8",
        )
        extra_chain_modules.append(module)
        previous_module = module
        previous_binding = binding
    for index in range(independent_modules):
        (source_root / f"independent-{index}.ss").write_text(
            f"(export value-{index})\n(def value-{index} {index})\n",
            encoding="utf-8",
        )
    modules = list(reversed(extra_chain_modules)) + ["leaf", "middle", "upstream"] + [
        f"independent-{index}" for index in range(independent_modules)
    ]
    quoted_modules = " ".join(f'\"{module}\"' for module in modules)
    (source_root / "build.ss").write_text(
        "(import :std/make)\n"
        f"(make '({quoted_modules})\n"
        "      srcdir: \".\"\n"
        "      libdir: (path-expand \"lib\" (getenv \"GERBIL_PATH\"))\n"
        "      bindir: (path-expand \"bin\" (getenv \"GERBIL_PATH\"))\n"
        "      parallelize: #t optimize: #f verbose: 3)\n",
        encoding="utf-8",
    )
    consumer_specs = [
        ("upstream", "value", 41),
        ("middle", "middle-value", 42),
        ("leaf", "answer", 42),
    ] + [
        (f"chain-{index}", f"chain-value-{index}", index + 40)
        for index in range(3, chain_modules)
    ] + [
        (f"independent-{index}", f"value-{index}", index)
        for index in range(independent_modules)
    ]
    consumer_statements = [
        f'(displayln "... consumer-observe event=start modules={len(consumer_specs)}")',
        "(force-output)",
    ]
    for index, (module, binding, expected) in enumerate(consumer_specs, start=1):
        module_id = f"std-make-scheduler-fixture/{module}"
        consumer_statements.extend(
            [
                f'(displayln "... consumer-observe event=load index={index} '
                f'module={module}")',
                "(force-output)",
                f'(load-module "{module_id}")',
                f"(let (actual (eval '{module_id}#{binding})) "
                f'(unless (= actual {expected}) '
                f'(error "consumer value mismatch" "{module}" actual)))',
            ]
        )
        if index % 10 == 0 or index == len(consumer_specs):
            consumer_statements.append(
                f'(displayln "... consumer-observe event=progress completed='
                f'{index} modules={len(consumer_specs)}")'
            )
            consumer_statements.append("(force-output)")
    consumer_statements.append(
        f'(displayln "... consumer-observe event=end status=passed modules='
        f'{len(consumer_specs)}")'
    )
    consumer_statements.append("(force-output)")
    (source_root / "consumer.ss").write_text(
        "\n".join(consumer_statements) + "\n", encoding="utf-8"
    )
    (source_root / "failure.ss").write_text(
        "(import :std/make)\n"
        "(make '(\"missing\")\n"
        "      srcdir: \".\"\n"
        "      libdir: (path-expand \"failure-lib\" (getenv \"GERBIL_PATH\"))\n"
        "      bindir: (path-expand \"failure-bin\" (getenv \"GERBIL_PATH\"))\n"
        "      parallelize: #t optimize: #f verbose: 3)\n",
        encoding="utf-8",
    )


def scheduler_observation(result: CommandResult) -> dict[str, Any]:
    compile_events = [
        event for event in result.events if "... compile " in str(event["line"])
    ]
    native_events = [
        event
        for event in result.events
        if "... execute compile job " in str(event["line"])
    ]
    enqueue_events = [
        event
        for event in result.events
        if "... enqueue compile job " in str(event["line"])
    ]
    native_job_kind_counts = {"compile-file": 0, "compile-batch": 0}
    invoke_count = 0
    for event in result.events:
        line = str(event["line"])
        for kind in native_job_kind_counts:
            native_job_kind_counts[kind] += line.count(
                f"execute compile job ({kind}"
            )
        invoke_count += line.count("invoke (")
    first_native_ns = native_events[0]["elapsedNs"] if native_events else None
    last_enqueue_ns = enqueue_events[-1]["elapsedNs"] if enqueue_events else None
    if first_native_ns is None or last_enqueue_ns is None:
        order = "unobserved"
    elif first_native_ns < last_enqueue_ns:
        order = "overlapped"
    else:
        order = "staged"
    return {
        "gerbilCompileAnnouncementCount": len(compile_events),
        "nativeJobEnqueueCount": len(enqueue_events),
        "nativeJobStartCount": sum(native_job_kind_counts.values()),
        "nativeJobKindCounts": native_job_kind_counts,
        "nativeCompilerInvocationCount": invoke_count,
        "firstNativeJobStartNs": first_native_ns,
        "lastNativeJobEnqueueNs": last_enqueue_ns,
        "observedOrder": order,
    }


BUILD_OBSERVATION = re.compile(
    r"\.\.\. build-observe (?P<body>.*?)(?=\.\.\. |$)"
)
BUILD_OBSERVATION_FIELD = re.compile(r"(?P<name>[A-Za-z][A-Za-z0-9]*)=(?P<value>\S+)")


def observation_value(value: str) -> str | int | bool:
    if value == "#t":
        return True
    if value == "#f":
        return False
    try:
        return int(value)
    except ValueError:
        return value


def build_observations(result: CommandResult) -> list[dict[str, Any]]:
    observations: list[dict[str, Any]] = []
    for event in result.events:
        line = str(event["line"])
        for match in BUILD_OBSERVATION.finditer(line):
            fields = {
                field.group("name"): observation_value(field.group("value"))
                for field in BUILD_OBSERVATION_FIELD.finditer(match.group("body"))
            }
            if "phase" in fields and "event" in fields:
                fields["elapsedNs"] = event["elapsedNs"]
                observations.append(fields)
    return observations


def derived_build_metrics(
    observations: Sequence[dict[str, Any]],
) -> dict[str, int | float | None]:
    native_end = next(
        (
            item
            for item in reversed(observations)
            if item.get("phase") == "native"
            and item.get("event") == "end"
            and "jobs" in item
        ),
        None,
    )
    build_end = next(
        (
            item
            for item in reversed(observations)
            if item.get("phase") == "build" and item.get("event") == "end"
        ),
        None,
    )
    if native_end is None:
        return {
            "nativeJobCount": None,
            "nativeAverageQueueMs": None,
            "nativeAverageExecutionMs": None,
            "nativeWallShare": None,
            "nativeWorkerUtilization": None,
        }

    jobs = int(native_end["jobs"])
    workers = int(native_end["workers"])
    native_wall_ms = int(native_end["wallMs"])
    build_wall_ms = int(build_end["elapsedMs"]) if build_end else 0
    queue_total_ms = int(native_end["queueTotalMs"])
    execution_total_ms = int(native_end["executionTotalMs"])
    return {
        "nativeJobCount": jobs,
        "nativeAverageQueueMs": queue_total_ms / jobs if jobs else None,
        "nativeAverageExecutionMs": execution_total_ms / jobs if jobs else None,
        "nativeWallShare": native_wall_ms / build_wall_ms if build_wall_ms else None,
        "nativeWorkerUtilization": (
            execution_total_ms / (workers * native_wall_ms)
            if workers and native_wall_ms
            else None
        ),
    }


def receipt_summary(receipt: dict[str, Any], receipt_path: Path) -> dict[str, Any]:
    """Return the terminal-sized decision surface; the file remains authoritative."""
    cold = receipt["cold"]
    return {
        "schema": receipt["schema"],
        "status": receipt["status"],
        "receipt": str(receipt_path),
        "coldElapsedMs": round(int(cold["elapsedNs"]) / 1_000_000, 3),
        "derivedMetrics": cold.get("derivedMetrics", {}),
        "failedAssertions": [
            item["name"] for item in receipt["assertions"] if not item["passed"]
        ],
    }


def artifact_manifest(output_root: Path, pattern: str) -> list[dict[str, Any]]:
    artifacts: list[dict[str, Any]] = []
    for path in sorted((output_root / "lib").rglob(pattern)):
        if not path.is_file():
            continue
        payload = path.read_bytes()
        artifacts.append(
            {
                "path": str(path.relative_to(output_root)),
                "bytes": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
        )
    return artifacts


def runtime_object_candidates(module_path: str) -> list[dict[str, Any]]:
    module = Path(module_path)
    stem = module.with_suffix("")
    candidates: list[dict[str, Any]] = []
    for path in sorted(stem.parent.glob(stem.name + ".o*")):
        if not path.is_file():
            continue
        payload = path.read_bytes()
        candidates.append(
            {
                "path": str(path.resolve()),
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
        )
    return candidates


def executable_identity(path: str) -> dict[str, Any]:
    resolved = Path(path).resolve()
    payload = resolved.read_bytes()
    return {
        "path": str(resolved),
        "bytes": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }


def probe_module_path(gxi: str, module: str, environment: dict[str, str]) -> str:
    expression = (
        "(import :gerbil/expander) "
        f"(displayln (core-resolve-library-module-path (quote :{module})))"
    )
    completed = subprocess.run(
        [gxi, "-e", expression],
        check=False,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise RuntimeError(f"cannot resolve :{module}: {detail}")
    return completed.stdout.strip()


def git_revision(repository: Path) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repository), "rev-parse", "HEAD"],
        check=True,
        stdout=subprocess.PIPE,
        text=True,
    )
    return completed.stdout.strip()


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gxi", default=os.environ.get("GERBIL_GXI"))
    parser.add_argument("--gsc", default=os.environ.get("GERBIL_GSC"))
    parser.add_argument("--gerbil-source", type=Path)
    parser.add_argument("--expected-compiler-root", type=Path)
    parser.add_argument("--expected-std-make-root", type=Path)
    parser.add_argument("--build-cores", type=int, default=available_cpu_count())
    parser.add_argument("--independent-modules", type=int, default=6)
    parser.add_argument("--chain-modules", type=int, default=3)
    parser.add_argument("--build-timeout", type=float, default=120.0)
    parser.add_argument("--consumer-timeout", type=float, default=120.0)
    parser.add_argument("--failure-timeout", type=float, default=3.0)
    parser.add_argument(
        "--expected-native-job-kind",
        choices=("compile-file", "compile-batch"),
        help="assert the scheduler behavior observed in the cold-build log",
    )
    parser.add_argument(
        "--receipt",
        type=Path,
        default=Path(".ci/receipts/std-make-scheduler.json"),
    )
    parser.add_argument("--keep-root", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str]) -> int:
    args = parse_args(argv)
    if args.build_cores < 1:
        raise RuntimeError("--build-cores must be positive")
    if args.independent_modules < 0:
        raise RuntimeError("--independent-modules must be non-negative")
    if args.consumer_timeout <= 0:
        raise RuntimeError("--consumer-timeout must be positive")
    if args.chain_modules < 3:
        raise RuntimeError("--chain-modules must be at least 3")
    gxi = resolve_executable(args.gxi, ("gxi",), name="gxi")
    gsc = resolve_gerbil_gsc(gxi, args.gsc)
    scenario_root = Path(tempfile.mkdtemp(prefix="gerbil-std-make-scheduler-"))
    source_root = scenario_root / "src"
    output_root = scenario_root / "output"
    write_fixture(source_root, args.independent_modules, args.chain_modules)
    environment = sanitize_build_environment(os.environ)
    environment.update(
        {
            "GERBIL_BUILD_CORES": str(args.build_cores),
            "GERBIL_PATH": str(output_root),
            "GERBIL_BUILD_VERBOSE": "3",
            "GERBIL_GSC": gsc,
        }
    )
    try:
        resolved_modules = {
            "compilerBase": probe_module_path(gxi, "gerbil/compiler/base", environment),
            "compilerDriver": probe_module_path(
                gxi, "gerbil/compiler/driver", environment
            ),
            "stdMake": probe_module_path(gxi, "std/make", environment),
        }
        gerbil_version = subprocess.run(
            [gxi, "--version"],
            check=False,
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        ).stdout.strip()
        gsc_version = subprocess.run(
            [gsc, "-v"],
            check=False,
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        ).stdout.strip()
        gerbil_revision = (
            git_revision(args.gerbil_source.resolve())
            if args.gerbil_source is not None
            else None
        )
        expected_roots = {
            "compilerBase": (
                str(args.expected_compiler_root.resolve())
                if args.expected_compiler_root is not None
                else None
            ),
            "compilerDriver": (
                str(args.expected_compiler_root.resolve())
                if args.expected_compiler_root is not None
                else None
            ),
            "stdMake": (
                str(args.expected_std_make_root.resolve())
                if args.expected_std_make_root is not None
                else None
            ),
        }
        overlay_loaded = all(
            root is None
            or str(Path(resolved_modules[name]).resolve()).startswith(root + os.sep)
            for name, root in expected_roots.items()
        )
        resolved_runtime_objects = {
            name: runtime_object_candidates(path)
            for name, path in resolved_modules.items()
        }
        runtime_objects_unambiguous = all(
            len(candidates) == 1
            for candidates in resolved_runtime_objects.values()
        )
        cold = run_timed(
            (gxi, "build.ss"),
            phase="cold",
            cwd=source_root,
            environment=environment,
            timeout_seconds=args.build_timeout,
        )
        warm = run_timed(
            (gxi, "build.ss"),
            phase="warm",
            cwd=source_root,
            environment=environment,
            timeout_seconds=args.build_timeout,
        )
        consumer = run_timed(
            (gxi, "consumer.ss"),
            phase="consumer",
            cwd=source_root,
            environment=environment,
            timeout_seconds=args.consumer_timeout,
        )
        failure = run_timed(
            (gxi, "failure.ss"),
            phase="coordinator-error",
            cwd=source_root,
            environment=environment,
            timeout_seconds=args.failure_timeout,
        )
        artifacts = artifact_manifest(output_root, "*.ssi")
        native_artifacts = artifact_manifest(output_root, "*.o*")
        cold_scheduler = scheduler_observation(cold)
        cold_observations = build_observations(cold)
        cold_derived_metrics = derived_build_metrics(cold_observations)
        expected_kind_observed = (
            args.expected_native_job_kind is None
            or cold_scheduler["nativeJobKindCounts"][args.expected_native_job_kind] > 0
        )
        unexpected_kinds_absent = args.expected_native_job_kind is None or all(
            count == 0
            for kind, count in cold_scheduler["nativeJobKindCounts"].items()
            if kind != args.expected_native_job_kind
        )
        assertions = [
            {"name": "module-overlay-resolved", "passed": overlay_loaded},
            {
                "name": "module-runtime-object-unambiguous",
                "passed": runtime_objects_unambiguous,
            },
            {
                "name": "binary-matches-source-revision",
                "passed": gerbil_revision is None or gerbil_revision[:7] in gerbil_version,
            },
            {
                "name": "cold-build-succeeded",
                "passed": cold.exit_code == 0 and not cold.timed_out,
            },
            {
                "name": "expected-native-job-kind-observed",
                "passed": expected_kind_observed,
            },
            {
                "name": "unexpected-native-job-kinds-absent",
                "passed": unexpected_kinds_absent,
            },
            {
                "name": "warm-build-succeeded",
                "passed": warm.exit_code == 0 and not warm.timed_out,
            },
            {
                "name": "fixture-consumer-succeeded",
                "passed": consumer.exit_code == 0 and not consumer.timed_out,
            },
            {
                "name": "fixture-artifacts-complete",
                "passed": len(artifacts)
                == args.chain_modules + args.independent_modules,
            },
            {
                "name": "fixture-native-artifacts-complete",
                "passed": len(native_artifacts)
                == 2 * (args.chain_modules + args.independent_modules),
            },
            {
                "name": "failure-path-observed",
                "passed": failure.timed_out or failure.exit_code != 0,
            },
        ]
        status = "passed" if all(item["passed"] for item in assertions) else "failed"
        receipt: dict[str, Any] = {
            "schema": SCHEMA,
            "status": status,
            "host": {
                "system": platform.system().lower(),
                "architecture": platform.machine().lower(),
                "availableLogicalCpuCount": available_cpu_count(),
            },
            "toolchain": {
                "gxi": gxi,
                "gxiExecutable": executable_identity(gxi),
                "gsc": gsc,
                "gscExecutable": executable_identity(gsc),
                "gscVersion": gsc_version,
                "gerbilVersion": gerbil_version,
                "gerbilRevision": gerbil_revision,
                "resolvedModules": resolved_modules,
                "resolvedRuntimeObjects": resolved_runtime_objects,
                "expectedModuleRoots": expected_roots,
            },
            "configuration": {
                "buildCores": args.build_cores,
                "independentModules": args.independent_modules,
                "chainModules": args.chain_modules,
                "buildTimeoutSeconds": args.build_timeout,
                "consumerTimeoutSeconds": args.consumer_timeout,
                "failureTimeoutSeconds": args.failure_timeout,
                "expectedNativeJobKind": args.expected_native_job_kind,
            },
            "cold": {
                "exitCode": cold.exit_code,
                "elapsedNs": cold.elapsed_ns,
                "timedOut": cold.timed_out,
                "scheduler": cold_scheduler,
                "observations": cold_observations,
                "derivedMetrics": cold_derived_metrics,
                "events": list(cold.events),
            },
            "warm": {
                "exitCode": warm.exit_code,
                "elapsedNs": warm.elapsed_ns,
                "timedOut": warm.timed_out,
                "eventCount": len(warm.events),
            },
            "consumer": {
                "exitCode": consumer.exit_code,
                "elapsedNs": consumer.elapsed_ns,
                "timedOut": consumer.timed_out,
                "events": list(consumer.events),
            },
            "failure": {
                "exitCode": failure.exit_code,
                "elapsedNs": failure.elapsed_ns,
                "timedOut": failure.timed_out,
                "events": list(failure.events),
            },
            "artifacts": artifacts,
            "nativeArtifacts": native_artifacts,
            "assertions": assertions,
        }
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        temporary = args.receipt.with_suffix(args.receipt.suffix + ".tmp")
        temporary.write_text(
            json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        temporary.replace(args.receipt)
        print(
            json.dumps(
                receipt_summary(receipt, args.receipt),
                separators=(",", ":"),
                sort_keys=True,
            )
        )
        return 0 if status == "passed" else 1
    finally:
        if args.keep_root:
            print(f"preserved scenario root: {scenario_root}", file=sys.stderr)
        else:
            shutil.rmtree(scenario_root)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
