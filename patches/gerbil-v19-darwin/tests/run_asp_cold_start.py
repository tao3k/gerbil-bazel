#!/usr/bin/env python3
"""Measure exact PR checkout startup and its official cold package lifecycle."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import struct
from threading import Thread
import time
from bazel_host_environment import build_environment


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--toolchain-source", type=Path, required=True)
    parser.add_argument("--binary-source", type=Path)
    parser.add_argument("--library-overlay", type=Path)
    parser.add_argument("--gambit-cost-trace", type=Path)
    parser.add_argument("--host-count-dir", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--head", required=True)
    parser.add_argument("--package-root", type=Path)
    parser.add_argument("--gambit-host-group-budget", type=int)
    parser.add_argument("--prepared-dependency-head")
    parser.add_argument("--clean-first", action="store_true")
    parser.add_argument("--build-entry-only", action="store_true")
    parser.add_argument("--package-name", choices=("asp-gerbil-scheme", "gerbil-mcp"),
                        default="asp-gerbil-scheme")
    parser.add_argument("--prepare-mcp", action="store_true")
    parser.add_argument("--no-dependencies", action="store_true")
    parser.add_argument("--strict-output-gap-seconds", type=float)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    if args.build_entry_only and not args.clean_first:
        parser.error("build-entry-only requires clean-first")
    if args.resume and (args.clean_first or args.build_entry_only):
        parser.error("clean-first requires a fresh measurement, not resume")
    if args.prepare_mcp and (args.package_name != "gerbil-mcp" or not args.build_entry_only):
        parser.error("prepare-mcp requires the MCP build-entry-only scenario")
    if args.no_dependencies and args.package_name != "gerbil-mcp":
        parser.error("no-dependencies is limited to the dependency-free MCP fixture")
    if args.strict_output_gap_seconds is not None and args.strict_output_gap_seconds <= 0:
        parser.error("strict output gap must be positive")
    if args.gambit_host_group_budget is not None and args.gambit_host_group_budget <= 0:
        parser.error("host group budget must be positive")
    repo = Path(__file__).resolve().parents[3]
    project, source, output = args.project.resolve(), args.toolchain_source.resolve(), args.output.resolve()
    if not project.is_relative_to(repo / ".data") or not output.is_relative_to(repo / ".data"):
        parser.error("project and output must stay inside project .data")
    actual = subprocess.check_output(["git", "-C", str(project), "rev-parse", "HEAD"], text=True).strip()
    if actual != args.head:
        parser.error("project head differs from requested PR identity")
    output.mkdir(parents=True, exist_ok=args.resume)
    env = build_environment()
    env.pop("GAMBIT_HOST_GROUP_BUDGET", None)
    env.pop("GAMBIT_DARWIN_COST_TRACE", None)
    env.pop("GAMBIT_HOST_COUNT_DIR", None)
    counter_dir = None
    if args.host_count_dir:
        counter_dir = args.host_count_dir.resolve()
        if not counter_dir.is_relative_to(repo / ".data") or counter_dir.exists():
            parser.error("host counters require a fresh directory under project .data")
        counter_dir.mkdir(parents=True)
        env["GAMBIT_HOST_COUNT_DIR"] = str(counter_dir)
    if args.gambit_cost_trace:
        trace = args.gambit_cost_trace.resolve()
        if not trace.is_relative_to(repo / ".data") or trace.exists():
            parser.error("cost trace must be a fresh file under project .data")
        env["GAMBIT_DARWIN_COST_TRACE"] = str(trace)
    if args.gambit_host_group_budget is not None:
        env["GAMBIT_HOST_GROUP_BUDGET"] = str(args.gambit_host_group_budget)
    for key in ("GERBIL_HOME", "GERBIL_LOADPATH", "GERBIL_GSC", "GAMBOPT", "GERBIL_BUILD_PREFIX"):
        env.pop(key, None)
    cores = os.cpu_count()
    package_root = args.package_root.resolve() if args.package_root else output / "gerbil-path"
    if not package_root.is_relative_to(repo / ".data"):
        parser.error("package root must stay inside project .data")
    home = source / "build"
    binary_home = args.binary_source.resolve() / "build" if args.binary_source else home
    overlay = args.library_overlay.resolve() if args.library_overlay else None
    if overlay and not overlay.is_relative_to(repo / ".data"):
        parser.error("library overlay must stay inside project .data")
    if args.binary_source and args.prepare_mcp:
        parser.error("prepare MCP separately; its Makefile overrides the shared runtime home")
    env.update(GERBIL_HOME=str(home), GERBIL_PATH=str(package_root),
               GERBIL_LOADPATH=":".join(map(str, [package_root / "lib", *([overlay] if overlay else []), home / "lib"])),
               GERBIL_GSC=str(home / "bin/gsc"),
               GAMBOPT=f"~~bin={home / 'bin'},~~lib={home / 'lib'},~~include={home / 'include'}",
               PATH=f"{binary_home / 'bin'}:{home / 'bin'}:{env['PATH']}", GERBIL_BUILD_CORES=str(cores),
               GERBIL_BUILD_VERBOSE="2", GERBIL_GCC=env["GERBIL_GNU_GCC"])
    macros = subprocess.check_output([env["CC"], "-dM", "-E", "-x", "c", os.devnull], env=env, text=True)
    if "#define __clang__" in macros or "#define __GNUC__ 16\n" not in macros:
        raise RuntimeError("real GNU GCC 16 required")
    command = []
    report = {"projectHead": actual, "cores": cores, "hostLoadStart": os.getloadavg(),
              "gambitHostGroupBudget": args.gambit_host_group_budget,
              "preparedDependencyHead": args.prepared_dependency_head,
              "cleanFirst": args.clean_first, "buildEntryOnly": args.build_entry_only,
              "packageName": args.package_name,
              "strictOutputGapSeconds": args.strict_output_gap_seconds,
              "performanceQualified": False, "qualified": False, "runs": [],
              "packageRoot": str(package_root.relative_to(repo)),
              "consumerEnvironment": True,
              "runtimeHome": str(home.relative_to(repo)),
              "binaryHome": str(binary_home.relative_to(repo)),
              "libraryOverlay": str(overlay.relative_to(repo)) if overlay else None,
              "toolchainBinarySha256": {name: hashlib.sha256((binary_home / "bin" / name).read_bytes()).hexdigest()
                                        for name in ("gxi", "gsc")}}
    if args.resume:
        current_binary_hashes = report["toolchainBinarySha256"]
        report = json.loads((output / "report.json").read_text())
        if report["projectHead"] != actual or report["cores"] != cores:
            parser.error("resume identity or hardware differs")
        if (report.get("gambitHostGroupBudget") != args.gambit_host_group_budget
                or report.get("preparedDependencyHead") != args.prepared_dependency_head
                or report["toolchainBinarySha256"] != current_binary_hashes):
            parser.error("resume compiler identity or host grouping budget differs")
        report.pop("failure", None)
        report["qualified"] = False

    def save():
        (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")

    def counters(pids):
        if counter_dir is None:
            return []
        rows = []
        for pid in pids:
            for path in sorted(counter_dir.glob(f"{pid}-*.counter")):
                data = path.read_bytes()
                if len(data) != 8:
                    raise RuntimeError("malformed native host counter")
                rows.append({"pid": pid, "module": path.name.split("-", 1)[1][:-8],
                             "entries": struct.unpack("<Q", data)[0]})
        return rows

    def run(name, argv, seconds=1800):
        completed = [row for row in report["runs"] if row["name"] == name and row.get("passed")]
        if args.resume and completed:
            return completed[-1]
        started = time.monotonic()
        events, peak_gcc, previous, progress = {
            "startedMonotonic": started,
            "startedRuntimeClock": time.clock_gettime(time.CLOCK_MONOTONIC),
        }, 0, "", started
        output_clock = {"last": started, "maximumGap": 0.0}
        process_observation = {"rows": [], "atSeconds": None}
        logfile = output / f"{name}.log"
        process_env = dict(env)
        if name.startswith("focused-tests"):
            process_env.pop("GERBIL_BUILD_VERBOSE", None)
        with logfile.open("w") as log:
            child = subprocess.Popen(command + argv, cwd=project, env=process_env, stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT, text=True, start_new_session=True)
            events["processPid"] = child.pid
            def collect():
                for line in child.stdout:
                    now = time.monotonic() - started
                    instant = time.monotonic()
                    gap = instant - output_clock["last"]
                    output_clock["maximumGap"] = max(output_clock["maximumGap"], gap)
                    if args.strict_output_gap_seconds is not None and gap > args.strict_output_gap_seconds:
                        events["productOutputGapViolationSeconds"] = gap
                    output_clock["last"] = instant
                    if "firstOutputSeconds" not in events:
                        events["firstOutputSeconds"] = now
                        print(f"FIRST-OUTPUT {name}: {now:.3f}s", flush=True)
                    if line.startswith("READY "):
                        events[line.strip()] = now
                    if line.startswith("... compile "):
                        if "firstCompileSeconds" not in events:
                            events["firstCompileSeconds"] = now
                            events["firstCompileRuntimeClock"] = time.clock_gettime(time.CLOCK_MONOTONIC)
                            print(f"FIRST-COMPILE {name}: {now:.3f}s", flush=True)
                            observed = process_observation
                            cpu_rows = observed["rows"]
                            events["firstCompileObservedProcessCpuSeconds"] = (
                                sum(entry["cpuSeconds"] for entry in cpu_rows) if cpu_rows else None)
                            events["firstCompileObservedProcesses"] = cpu_rows
                            events["firstCompileCpuObservationAtSeconds"] = observed["atSeconds"]
                            events["firstCompileHostEntries"] = counters(
                                [row["pid"] for row in cpu_rows])
                    log.write(line)
                    log.flush()
                events["wallSeconds"] = time.monotonic() - started
            reader = Thread(target=collect, daemon=True)
            reader.start()
            descendants = {child.pid}
            discovered_at = 0.0
            previous_bytes = 0
            try:
                while child.poll() is None:
                    time.sleep(1)
                    if (args.strict_output_gap_seconds is not None
                            and (time.monotonic() - output_clock["last"] > args.strict_output_gap_seconds
                                 or "productOutputGapViolationSeconds" in events)):
                        raise TimeoutError(f"{name}: product output gap exceeded {args.strict_output_gap_seconds}s")
                    try:
                        if time.monotonic() - discovered_at >= 5:
                            rows = [line.split() for line in subprocess.check_output(
                                ["/bin/ps", "-axo", "pid,ppid"], text=True, timeout=1).splitlines()[1:]]
                            descendants = {child.pid}
                            for _ in range(10):
                                descendants.update(int(row[0]) for row in rows if len(row) == 2 and int(row[1]) in descendants)
                            discovered_at = time.monotonic()
                        rows = [line.split(None, 3) for line in subprocess.check_output(
                            ["/bin/ps", "-p", ",".join(map(str, sorted(descendants))),
                             "-o", "pid,pgid,time,comm"], text=True, timeout=1).splitlines()[1:]]
                        own = [row for row in rows if len(row) == 4 and int(row[1]) == child.pid]
                    except subprocess.TimeoutExpired:
                        events["processObservationTimeouts"] = events.get("processObservationTimeouts", 0) + 1
                        own = []
                    except subprocess.CalledProcessError:
                        if child.poll() is None:
                            raise
                        own = []
                    if own:
                        process_observation = {
                            "atSeconds": time.monotonic() - started,
                            "rows": [{"pid": int(row[0]), "command": Path(row[3]).name,
                                      "cpuSeconds": sum(float(part) * 60 ** index for index, part in
                                                        enumerate(reversed(row[2].split(":"))))}
                                     for row in own]}
                        events["lastObservedProcessCpuSeconds"] = sum(
                            entry["cpuSeconds"] for entry in process_observation["rows"])
                        events["lastObservedCpuAtSeconds"] = process_observation["atSeconds"]
                    if own and counter_dir is not None and "firstCompileSeconds" not in events:
                        events.setdefault("preCompileHostSamples", []).append({
                            "atSeconds": events["lastObservedCpuAtSeconds"],
                            "cpuSeconds": events["lastObservedProcessCpuSeconds"],
                            "counts": counters(descendants)})
                    count = sum(Path(row[3]).name == "cc1" for row in own)
                    peak_gcc = max(peak_gcc, count)
                    if count:
                        events.setdefault("firstGccSampleSeconds", time.monotonic() - started)
                    size = logfile.stat().st_size
                    if size != previous_bytes or (own and repr(own) != previous):
                        progress = time.monotonic()
                    if own:
                        previous = repr(own)
                    previous_bytes = size
                    if int(time.monotonic() - started) % 5 == 0:
                        print(f"PROGRESS {name}: {logfile.stat().st_size} bytes, peak GCC {peak_gcc}", flush=True)
                    if time.monotonic() - progress > 10 or time.monotonic() - started > seconds:
                        raise TimeoutError(f"{name}: stalled or exceeded budget")
                    if (args.strict_output_gap_seconds is not None
                            and (time.monotonic() - output_clock["last"] > args.strict_output_gap_seconds
                                 or "productOutputGapViolationSeconds" in events)):
                        raise TimeoutError(f"{name}: product output gap exceeded {args.strict_output_gap_seconds}s")
                status = child.wait()
                reader.join(timeout=5)
            except BaseException as error:
                if child.poll() is None:
                    os.killpg(child.pid, signal.SIGTERM)
                    try:
                        child.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        os.killpg(child.pid, signal.SIGKILL)
                        child.wait()
                reader.join(timeout=5)
                report["runs"].append({"name": name, "passed": False, "aborted": True,
                                       "failure": repr(error), **events})
                save()
                raise
        content = logfile.read_text(errors="replace")
        row = {"name": name, "exitCode": status, "passed": status == 0 and "*** ERROR" not in content
               and "productOutputGapViolationSeconds" not in events,
               "peakConcurrentGccFrontends": peak_gcc, "log": logfile.name, **events}
        row["maximumOutputGapSeconds"] = max(output_clock["maximumGap"], time.monotonic() - output_clock["last"])
        print(f"{'OK' if row['passed'] else 'FAIL'} {name}: {events['wallSeconds']:.3f}s", flush=True)
        return row

    def stage(name, argv, seconds=1800):
        row = run(name, argv, seconds)
        if row not in report["runs"]:
            report["runs"].append(row)
        save()
        if not row["passed"]:
            raise RuntimeError(f"{name} failed; inspect {row['log']}")

    try:
        save()
        if args.prepare_mcp:
            stage("mcp-preparation", ["make", "compat", "regex", "embedded-data",
                                      "check-gerbil", "check-version", f"GERBIL={home / 'bin/gerbil'}"])
        if args.package_name == "gerbil-mcp":
            report["mcpPreparationInvoked"] = args.prepare_mcp
            report["preparedSourceSha256"] = {
                name: hashlib.sha256((project / name).read_bytes()).hexdigest()
                for name in ("util/compat.ss", "util/regex.ss", "data/embedded.ss", "build.ss")}
            save()
        if args.prepared_dependency_head:
            dependency = package_root / "pkg/github.com/tao3k/gerbil-poo"
            head = subprocess.check_output(["git", "-C", str(dependency), "rev-parse", "HEAD"], text=True).strip()
            manifest = (project / "gerbil.pkg").read_text()
            if head != args.prepared_dependency_head or f"gerbil-poo@{head}" not in manifest:
                raise RuntimeError("prepared dependency does not match project's immutable pin")
            if (package_root / "lib" / args.package_name).exists() and not args.clean_first:
                raise RuntimeError("prepared dependency root contains prior project artifacts")
            print(f"DEPENDENCY-OK pinned local source {head}", flush=True)
            report["preparedDependencyVerified"] = True
            save()
        elif args.no_dependencies:
            manifest = json.dumps(str(project / "gerbil.pkg"))
            expression = f'''(let ((fields (call-with-input-file {manifest} read)))
              (let loop ((rest fields))
                (cond ((null? rest) (display "DEPENDENCIES-EMPTY") (newline))
                      ((and (pair? rest) (pair? (cdr rest)) (keyword? (car rest))
                            (member (keyword->string (car rest))
                                    '("package" "version" "description")))
                       (loop (cddr rest)))
                      (else (error "manifest has unqualified dependency fields")))))'''
            stage("dependency-free-manifest", [str(home / "bin/gsc"), "-e", expression], 30)
            if "DEPENDENCIES-EMPTY" not in (output / "dependency-free-manifest.log").read_text():
                raise RuntimeError("MCP manifest was not verified dependency-free")
            report["dependencyInstallationSkipped"] = True
            save()
        else:
            stage("dependencies", ["gerbil", "deps", "--install"])
        if args.clean_first:
            native_root = package_root / "lib" / args.package_name
            report["projectNativeImagesBeforeClean"] = len(list(native_root.rglob("*.o1")))
            stage("official-clean", ["gerbil", "clean"])
            report["projectNativeImagesAfterClean"] = len(list(native_root.rglob("*.o1")))
            save()
            if report["projectNativeImagesAfterClean"]:
                raise RuntimeError("official clean left project native images")
        if args.build_entry_only:
            stage("cold-build", ["gerbil", "build"])
            cold = report["runs"][-1]
            if "firstCompileSeconds" not in cold:
                raise RuntimeError("clean build emitted no compilation log")
            report["qualified"] = True
            report["qualificationScope"] = "official-clean-build-first-log-only"
            report["projectNativeImagesAfterBuild"] = len(list(native_root.rglob("*.o1")))
            save()
            return
        for label, expression in (
            ("make-import", '(displayln "READY runtime") (force-output) (eval \'(import :std/make)) (displayln "READY make") (force-output)'),
            ("source-bootstrap", '(displayln "READY runtime") (force-output) (eval \'(import "./src/build-api/source-bootstrap")) (displayln "READY source-bootstrap") (force-output)')):
            entry = ["gerbil", "env", "gxi"] if label == "source-bootstrap" else ["gxi"]
            with ThreadPoolExecutor(max_workers=cores) as pool:
                futures = [pool.submit(run, f"{label}-{index}", entry + ["-e", expression], 120) for index in range(cores)]
                rows = [future.result() for future in futures]
            report["runs"].extend(row for row in rows if row not in report["runs"])
            save()
            if not all(row["passed"] and f"READY {'make' if label == 'make-import' else 'source-bootstrap'}" in row for row in rows):
                raise RuntimeError(f"{label} did not reach readiness")
        stage("entry-meta", ["gerbil", "env", "gxi", "build.ss", "meta"])
        stage("cold-build", ["gerbil", "build"])
        stage("warm-build", ["gerbil", "build"])
        stage("direct-meta", ["gxi", "build.ss", "meta"])
        stage("direct-warm-build", ["gxi", "build.ss", "compile"])
        test_expression = "(import :gerbil/tools/gxtest) (exit (apply main (cdddr (command-line))))"
        stage("focused-tests-direct", ["gxi", "-e", test_expression,
                               "t/build-script-command-test.ss", "t/package-build-contract-test.ss",
                               "t/build-api-source-bootstrap-test.ss", "t/build-api-startup-scenario-test.ss"])
        tests = (output / "focused-tests-direct.log").read_text()
        if "HARNESS-OK" not in tests or tests.count("MODULE-OK") != 4 or not tests.rstrip().endswith("OK"):
            raise RuntimeError("all four focused upstream modules must qualify")
        report["qualified"] = True
        report["finalTestLog"] = "focused-tests-direct.log"
    except BaseException as error:
        report["failure"] = str(error)
        raise
    finally:
        report["hostLoadEnd"] = os.getloadavg()
        save()


if __name__ == "__main__":
    main()
