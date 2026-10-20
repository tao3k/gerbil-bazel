#!/usr/bin/env python3
"""Paired CPU diagnostic for the real build framework/compiler imports."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import resource
import re
import subprocess
import time

from bazel_host_environment import build_environment


def parse_process_statistics(content):
    matches = re.findall(r"^GAMBIT-PROCESS-STATISTICS \(([^\n]*)\)$", content, re.MULTILINE)
    if len(matches) != 1:
        raise RuntimeError("missing or ambiguous native process statistics")
    values = [float(item) for item in matches[0].split()]
    if len(values) != 20 or not all(math.isfinite(item) and item >= 0 for item in values):
        raise RuntimeError("invalid native process statistics layout")
    return {"values": values, "userCpuSeconds": values[0], "systemCpuSeconds": values[1],
            "gcUserCpuSeconds": values[3], "gcSystemCpuSeconds": values[4],
            "gcCount": values[6], "allocatedBytes": values[7],
            "latestGcHeapBytes": values[15], "latestGcLiveBytes": values[17],
            "layoutSource": "src/gambit/lib/_kernel.scm:##process-statistics"}


def parse_fresh_tree_counts(content):
    sites = []
    seen = set()
    for line in content.splitlines():
        values = line.split()
        if len(values) != 4 or any(not value.isdecimal() for value in values):
            raise RuntimeError('invalid fresh tree count row')
        site, commits, words, rollback_words = map(int, values)
        if (not 0 <= site < 256 or site in seen or not commits <= words <= 64*commits):
            raise RuntimeError('inconsistent fresh tree counters')
        seen.add(site)
        sites.append(dict(site=site, allocatedReturns=commits,
                          committedHeapWords=words, rolledBackHeapWords=rollback_words))
    return dict(sites=sites, allocatedReturns=sum(row['allocatedReturns'] for row in sites),
                committedHeapWords=sum(row['committedHeapWords'] for row in sites),
                rolledBackHeapWords=sum(row['rolledBackHeapWords'] for row in sites),
                scope='actual-completed-allocation-path-counts-not-speedup')


def parse_scalar_elided_words(content):
    values = content.split()
    if len(values) != 1 or not values[0].isdecimal():
        raise RuntimeError('invalid scalar elision counter')
    return dict(elidedHeapWords=int(values[0]),
                scope='actual-scalarized-return-words-not-speedup-or-gross-allocation-delta')


def parse_hash_scan_counts(content):
    values = content.split()
    if len(values) != 9 or any(not value.isdecimal() for value in values):
        raise RuntimeError('invalid hash scan counters')
    entries, selected, hits, misses, *sizes = map(int, values)
    if not (entries > 0 and 0 <= selected <= entries and hits+misses == selected
            and sum(sizes) == entries):
        raise RuntimeError('inconsistent hash scan counters')
    return dict(entries=entries, selected=selected, hits=hits, misses=misses,
                capacityBuckets=sizes, capacityUpperBounds=[8, 32, 128, 512, None],
                scope='actual-live-table-scan-coverage-not-speedup')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--build-script", type=Path)
    parser.add_argument("--baseline-binary-source", type=Path)
    parser.add_argument("--prepare-imports", action="store_true")
    parser.add_argument("--edge-trace-dir", type=Path)
    parser.add_argument("--candidate-only", action="store_true")
    parser.add_argument("--structure-trace-dir", type=Path)
    parser.add_argument("--kernel-label-dir", type=Path)
    parser.add_argument("--complete-toolchain", action="store_true")
    parser.add_argument("--wall-budget", type=int, default=60)
    parser.add_argument("--gc-hash-probe-file", type=Path)
    parser.add_argument("--gc-mark-probe-file", type=Path)
    parser.add_argument("--process-statistics", action="store_true")
    parser.add_argument("--source-cost-prefix", type=Path)
    parser.add_argument("--trace-count-file", type=Path)
    parser.add_argument("--hash-scan-count-file", type=Path)
    parser.add_argument("--native-pc-sample", action="store_true")
    parser.add_argument("--native-pc-profile", type=Path)
    parser.add_argument("--native-pc-seconds", type=int, default=2)
    args = parser.parse_args()
    if not 60 <= args.wall_budget <= 180:
        parser.error("CPU-only wall budget must be between 60 and 180 seconds")
    if not 2 <= args.native_pc_seconds <= 10:
        parser.error("native PC observation must be between two and ten seconds")
    if args.native_pc_seconds != 2 and not args.native_pc_sample:
        parser.error("native PC observation duration requires native sampling")
    if args.baseline_binary_source and args.complete_toolchain:
        parser.error("a baseline binary override is only a shared-home runtime comparison")
    if args.prepare_imports and not args.build_script:
        parser.error("module preparation requires the original build script")
    if args.gc_hash_probe_file and not args.candidate_only:
        parser.error("hash counter observations cannot be performance comparisons")
    if args.gc_mark_probe_file and not args.candidate_only:
        parser.error("GC marker observations cannot be performance comparisons")
    if args.trace_count_file and not args.candidate_only:
        parser.error("trace counter observations cannot be performance comparisons")
    if args.hash_scan_count_file and (not args.candidate_only or args.trace_count_file):
        parser.error("hash scan counts require a separate candidate-only diagnostic")
    if args.native_pc_sample:
        if not (args.candidate_only and args.prepare_imports):
            parser.error("native PC sampling requires a single diagnostic preparation run")
        profile_path = (args.native_pc_profile.resolve() if args.native_pc_profile
                        else args.candidate.resolve().parent)
        if not profile_path.is_relative_to(Path(__file__).resolve().parents[3] / ".data"):
            parser.error("native PC profile must stay under project .data")
        profile = json.loads((profile_path / "report.json").read_text())
        if not (profile.get("qualified") and profile.get("diagnosticOnly") and profile.get("nativePcLandmarks")):
            parser.error("native PC sampling requires a qualified PC-landmark diagnostic binary")
        if profile.get("binaryHashes", {}).get("gxi") != hashlib.sha256(
                (args.candidate.resolve() / "build/bin/gxi").read_bytes()).hexdigest():
            parser.error("native PC profile binary hash does not match candidate")
    elif args.native_pc_profile:
        parser.error("native PC profile is only valid for native sampling")
    if args.candidate_only and not (args.edge_trace_dir or args.structure_trace_dir or args.kernel_label_dir or args.gc_hash_probe_file or args.gc_mark_probe_file or args.trace_count_file or args.native_pc_sample or args.process_statistics):
        parser.error("single-candidate execution is only an edge diagnostic, not a CPU comparison")
    repo = Path(__file__).resolve().parents[3]
    output = args.output.resolve()
    if args.source_cost_prefix:
        if not (args.candidate_only and args.process_statistics):
            parser.error("source cost requires a single native-statistics diagnostic run")
        cost_prefix = args.source_cost_prefix.resolve()
        if not cost_prefix.is_relative_to(output) or list(cost_prefix.parent.glob(cost_prefix.name + '.*')):
            parser.error("source cost prefix must be fresh under diagnostic output")
    if not output.is_relative_to(repo / ".data"):
        parser.error("diagnostic must stay under project .data")
    output.mkdir(parents=True, exist_ok=False)
    if args.gc_hash_probe_file:
        probe_path = args.gc_hash_probe_file.resolve()
        if not probe_path.is_relative_to(output) or probe_path.exists():
            parser.error("hash probe receipt must be fresh and inside this output")
    env_mark = None
    if args.gc_mark_probe_file:
        env_mark = args.gc_mark_probe_file.resolve()
        if not env_mark.is_relative_to(output) or env_mark.exists():
            parser.error("GC marker receipt must be fresh and inside this output")
    home = args.baseline.resolve() / "build"
    binaries = {"baseline": home / "bin/gxi",
                "candidate": args.candidate.resolve() / "build/bin/gxi"}
    if args.baseline_binary_source:
        baseline_binary = args.baseline_binary_source.resolve()
        if not baseline_binary.is_relative_to(repo / ".data"):
            parser.error("baseline binary must stay under project .data")
        binaries["baseline"] = baseline_binary / "build/bin/gxi"
    homes = {"baseline": home,
             "candidate": args.candidate.resolve() / "build" if args.complete_toolchain else home}
    env = build_environment()
    for key in ("GAMBIT_HOST_COUNT_DIR", "GAMBIT_DARWIN_COST_TRACE",
                "GAMBIT_HOST_GROUP_BUDGET", "GERBIL_BUILD_PREFIX", "GERBIL_GSC"):
        env.pop(key, None)
    env.pop("GAMBIT_PRIVATE_EDGE_DIR", None)
    env.pop("GAMBIT_STRUCTURE_PRIMITIVE_DIR", None)
    env.pop("GAMBIT_KERNEL_LABEL_DIR", None)
    env.pop("GAMBIT_TRACE_COUNT_FILE", None)
    env.pop("GAMBIT_GC_MARK_PROBE_FILE", None)
    env.pop("GAMBIT_DARWIN_SOURCE_COST_PREFIX", None)
    if args.source_cost_prefix:
        env["GAMBIT_DARWIN_SOURCE_COST_PREFIX"] = str(cost_prefix)
    if env_mark:
        env["GAMBIT_GC_MARK_PROBE_FILE"] = str(env_mark)
    if args.trace_count_file:
        trace = args.trace_count_file.resolve()
        if not trace.is_relative_to(output) or trace.exists():
            parser.error("trace counts require a fresh file within this output")
        env["GAMBIT_TRACE_COUNT_FILE"] = str(trace)
    if args.hash_scan_count_file:
        scan_prefix = args.hash_scan_count_file.resolve()
        scan_file = scan_prefix.with_name(scan_prefix.name+'.hash-scan')
        if not scan_prefix.is_relative_to(output) or scan_prefix.exists() or scan_file.exists():
            parser.error("hash scan counts require a fresh prefix within this output")
        env["GAMBIT_TRACE_COUNT_FILE"] = str(scan_prefix)
    if args.kernel_label_dir:
        trace = args.kernel_label_dir.resolve()
        if not trace.is_relative_to(repo / ".data") or trace.exists():
            parser.error("kernel labels require fresh project .data output")
        trace.mkdir(parents=True)
        env["GAMBIT_KERNEL_LABEL_DIR"] = str(trace)
    if args.structure_trace_dir:
        trace = args.structure_trace_dir.resolve()
        if not trace.is_relative_to(repo / ".data") or trace.exists():
            parser.error("structure trace must be fresh under project .data")
        trace.mkdir(parents=True)
        env["GAMBIT_STRUCTURE_PRIMITIVE_DIR"] = str(trace)
    if args.edge_trace_dir:
        trace = args.edge_trace_dir.resolve()
        if not trace.is_relative_to(repo / ".data") or trace.exists():
            parser.error("edge trace must be a fresh directory under project .data")
        trace.mkdir(parents=True)
        env["GAMBIT_PRIVATE_EDGE_DIR"] = str(trace)
    env.update(GERBIL_HOME=str(home), GERBIL_LOADPATH=str(home / "lib"),
               GERBIL_BUILD_CORES=str(os.cpu_count()),
               GAMBOPT=f"~~bin={home / 'bin'},~~lib={home / 'lib'},~~include={home / 'include'}")
    expression = '(import :std/make :std/build-script :std/test :gerbil/compiler) (displayln "IMPORT-OK")'
    if args.build_script:
        script = args.build_script.resolve()
        if not script.is_relative_to(repo / ".data"):
            parser.error("script input must stay under project .data")
        expression = f'(include {json.dumps(str(script))}) (displayln "IMPORT-OK")'
        if args.prepare_imports:
            root = json.dumps(str(script.parent))
            expression = f'''(import :gerbil/expander :gerbil/runtime/syntax)
(include {json.dumps(str(script))})
(let* ((forms (map gx#syntax->datum (read-syntax-from-file {json.dumps(str(script))})))
       (form (let lp ((rest forms))
               (cond ((null? rest) (error "missing build spec"))
                     ((and (pair? (car rest)) (eq? (caar rest) 'defbuild-script)) (car rest))
                     (else (lp (cdr rest))))))
       (spec (cadr (cadr form))))
  (parameterize ((current-directory {root}) (gx#current-expander-compiling? #t))
    (add-load-path! {root})
    (for-each (lambda (item)
                (let ((stem (cond ((string? item) item)
                                  ((and (pair? item) (eq? (car item) exe:)) (cadr item))
                                  (else (error "unsupported diagnostic spec" item)))))
                  (gx#import-module (path-expand (string-append stem ".ss") {root}) #f #f)
                  (displayln "PREPARED " stem)
                  (force-output)))
              spec))
  (displayln "MODULES " (length spec)))
(displayln "IMPORT-OK")'''
    if args.process_statistics:
        expression += '''
(let ((stats (##process-statistics)))
  (display "GAMBIT-PROCESS-STATISTICS ")
  (write (f64vector->list stats))
  (newline)
  (force-output))'''
    report = {"scope": "paired-import-CPU-diagnostic-not-official-cold-build",
              "performanceQualified": False, "qualified": False, "runs": [],
              "expression": expression,
              "buildScriptInvoked": False,
              "preparationImports": args.prepare_imports,
              "completeToolchain": args.complete_toolchain,
              "baselineBinaryOverride": str(baseline_binary.relative_to(repo)) if args.baseline_binary_source else None,
              "runtimeHomes": {key: str(path.relative_to(repo)) for key, path in homes.items()},
              "compilerHashes": {key: hashlib.sha256((path / "bin/gsc").read_bytes()).hexdigest()
                                 for key, path in homes.items()},
              "scriptSha256": hashlib.sha256(script.read_bytes()).hexdigest() if args.build_script else None,
              "binaryHashes": {key: hashlib.sha256(path.read_bytes()).hexdigest()
                               for key, path in binaries.items()}}
    report["cpuDiagnosticWallBudgetSeconds"] = args.wall_budget
    report["nativePcSamples"] = []
    samplers = []
    sample_logs = []
    if args.candidate_only:
        report["scope"] = "single-candidate-edge-diagnostic-not-performance"
        if args.process_statistics:
            report["scope"] = "single-candidate-native-process-statistics-not-performance"
        if args.kernel_label_dir:
            report["scope"] = "single-candidate-kernel-label-diagnostic-not-performance"
        if args.gc_mark_probe_file:
            report["scope"] = "single-candidate-gc-mark-counts-not-performance"
        if args.native_pc_sample:
            report["scope"] = "single-candidate-native-pc-diagnostic-not-performance"
            report["cpuTimesIncludeSampler"] = True
    try:
        # Sequential ABBA avoids own-test CPU contention and alternates ordering.
        order = ("candidate",) if args.candidate_only else ("baseline", "candidate", "candidate", "baseline")
        for index, key in enumerate(order):
            runtime = homes[key]
            if args.gc_hash_probe_file:
                env["GAMBIT_GC_HASH_PROBE_FILE"] = str(probe_path)
            env.update(GERBIL_HOME=str(runtime), GERBIL_LOADPATH=str(runtime / "lib"),
                       GERBIL_GSC=str(runtime / "bin/gsc"),
                       GAMBOPT=f"~~bin={runtime / 'bin'},~~lib={runtime / 'lib'},~~include={runtime / 'include'}")
            env["GERBIL_PATH"] = str(output / f"empty-{index}")
            before = resource.getrusage(resource.RUSAGE_CHILDREN)
            started = time.monotonic()
            log_path = output / f"{index}-{key}.log"
            with log_path.open("w") as log:
                child = subprocess.Popen([str(binaries[key]), "-e", expression], env=env,
                                         stdout=log, stderr=subprocess.STDOUT)
                try:
                    while child.poll() is None:
                        try:
                            child.wait(timeout=0.5 if args.native_pc_sample else 5)
                        except subprocess.TimeoutExpired:
                            if not args.native_pc_sample:
                                print(f"CPU-DIAGNOSTIC-ACTIVE {key}: {time.monotonic() - started:.1f}s, "
                                      f"{log_path.stat().st_size} recorded progress bytes", flush=True)
                        if args.native_pc_sample and child.poll() is None:
                            prepared = sum(line.startswith("PREPARED ") for line in log_path.read_text().splitlines())
                            index = len(samplers)
                            if index < 2 and prepared >= (10, 80)[index] and (not samplers or samplers[-1].poll() is not None):
                                destination = output / f"native-pc-{index}.sample.txt"
                                sample_log = (output / f"native-pc-{index}.log").open("w")
                                sample_logs.append(sample_log)
                                samplers.append(subprocess.Popen(
                                    ["/usr/bin/sample", str(child.pid), str(args.native_pc_seconds), "1", "-file", str(destination)],
                                    stdout=sample_log, stderr=subprocess.STDOUT))
                                report["nativePcSamples"].append({"preparedModulesAtStart": prepared,
                                    "startSeconds": time.monotonic() - started,
                                    "observationSeconds": args.native_pc_seconds, "file": destination.name})
                                print(f"NATIVE-PC-SAMPLE {index}: {prepared} real modules prepared", flush=True)
                        if child.poll() is None and time.monotonic() - started > args.wall_budget:
                            raise TimeoutError(f"CPU diagnostic exceeded {args.wall_budget}-second wall budget")
                finally:
                    if child.poll() is None:
                        child.kill()
                        child.wait()
            after = resource.getrusage(resource.RUSAGE_CHILDREN)
            content = log_path.read_text()
            row = {"binary": key, "wallSeconds": time.monotonic() - started,
                   "userCpuSeconds": after.ru_utime - before.ru_utime,
                   "systemCpuSeconds": after.ru_stime - before.ru_stime,
                   "hostLoad": os.getloadavg(), "exitCode": child.returncode,
                   "preparedModules": sum(line.startswith("PREPARED ") for line in content.splitlines())}
            report["runs"].append(row)
            if args.source_cost_prefix:
                path = cost_prefix.with_name(f"{cost_prefix.name}.{child.pid}.json")
                costs = json.loads(path.read_text())
                if (costs.get("pid") != child.pid or costs.get("errors") != 0
                        or costs.get("openFrames") != 0
                        or [p.get("kind") for p in costs.get("phases", [])] != list(range(4))
                        or any(p["calls"] <= 0 or any(p[field] < -0.000001 for field in (
                            "inclusiveUser", "inclusiveSystem", "inclusiveWall",
                            "exclusiveUser", "exclusiveSystem", "exclusiveWall"))
                               for p in costs["phases"])):
                    raise RuntimeError("incomplete or inconsistent source cost boundaries")
                report["nativeSourceCosts"] = costs
                report["sourceCostScope"] = "exclusive nested-boundary diagnostic, includes observer overhead"
            if args.gc_hash_probe_file:
                probe = json.loads(probe_path.read_text())
                if (probe["calls"] <= 0 or probe["steps"] < probe["calls"]
                        or sum(probe["stepHistogram"]) != probe["calls"]
                        or probe["hits"] + probe["misses"] != probe["calls"]):
                    raise RuntimeError("incomplete native hash probe counts")
                report["nativeHashProbeCounts"] = probe
            if args.gc_mark_probe_file:
                probe = json.loads(env_mark.read_text())
                if (probe["calls"] <= 0 or not 0 <= probe["singleCalls"] <= probe["calls"]
                        or not 0 <= probe["allocatedVisits"] <= probe["visits"]
                        or len(probe["heads"]) != 8 or len(probe["copiesBySubtype"]) != 32
                        or len(probe["wordsBySubtype"]) != 32 or len(probe["copySizeBuckets"]) != 10
                        or sum(probe["heads"]) != probe["allocatedVisits"]
                        or sum(probe["copiesBySubtype"]) != probe["heads"][0]
                        or sum(probe["copySizeBuckets"]) != probe["heads"][0]):
                    raise RuntimeError("incomplete GC marker counts")
                report["nativeGcMarkCounts"] = probe
            print(f"CPU-DIAGNOSTIC {key}: {row}", flush=True)
            checked_content = content
            if args.process_statistics:
                row["nativeProcessStatistics"] = parse_process_statistics(content)
                checked_content = re.sub(r"^GAMBIT-PROCESS-STATISTICS \([^\n]*\)\n", "", content, flags=re.MULTILINE)
            if args.candidate_only and args.structure_trace_dir:
                aliases = re.findall(r"^GEN-LABEL-ALIASES (\d+)$", content, re.MULTILINE)
                if aliases:
                    if len(aliases) != 1:
                        raise RuntimeError("ambiguous native-entry diagnostic trailer")
                    row["nativeEntryLabelAliases"] = int(aliases[0])
                    checked_content = re.sub(r"^GEN-LABEL-ALIASES \d+\n", "", content, flags=re.MULTILINE)
            if child.returncode or not checked_content.strip().endswith("IMPORT-OK"):
                raise RuntimeError("framework/compiler import contract failed")
        if args.trace_count_file:
            if not args.trace_count_file.is_file() or not args.trace_count_file.read_text().strip():
                raise RuntimeError("trace diagnostic must record actual attempts")
            fresh_counts = args.trace_count_file.with_name(args.trace_count_file.name+'.fresh-trees')
            if fresh_counts.is_file():
                report['freshTreeCounts'] = parse_fresh_tree_counts(fresh_counts.read_text())
            scalar_counts = args.trace_count_file.with_name(args.trace_count_file.name+'.scalar-elided-words')
            if scalar_counts.is_file():
                report['scalarElisionCounts'] = parse_scalar_elided_words(scalar_counts.read_text())
        if args.hash_scan_count_file:
            report['nativeHashScanCounts'] = parse_hash_scan_counts(scan_file.read_text())
        report["qualified"] = True
    except BaseException as error:
        report["failure"] = str(error)
        raise
    finally:
        for index, sampler in enumerate(samplers):
            try:
                sampler.wait(timeout=30)
            except subprocess.TimeoutExpired:
                sampler.kill()
                sampler.wait()
            report["nativePcSamples"][index]["exitCode"] = sampler.returncode
        for log in sample_logs:
            log.close()
        (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
