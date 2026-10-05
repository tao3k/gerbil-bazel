#!/usr/bin/env python3
"""Exercise the new toolchain with concurrent startup and std/make contracts."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
from threading import Thread
import time
from bazel_host_environment import build_environment


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repeats", type=int, default=2)
    parser.add_argument("--native-binary", action="store_true")
    parser.add_argument("--binary-source", type=Path)
    parser.add_argument("--library-overlay", type=Path)
    parser.add_argument("--strict-product-progress", action="store_true")
    args = parser.parse_args()
    if args.binary_source and not args.native_binary:
        parser.error("binary-source requires native-binary")
    cores = os.cpu_count()
    if not cores or cores < 2:
        parser.error("this parallel scenario requires at least two hardware threads")
    repo = Path(__file__).resolve().parents[3]
    source, output = args.source.resolve(), args.output.resolve()
    if not output.is_relative_to(repo / ".data") or args.repeats < 1:
        parser.error("use a fresh project .data directory and positive repeats")
    output.mkdir(parents=True)
    fixture = output / "fixture"
    fixture.mkdir()
    (fixture / "gerbil.pkg").write_text("(package: d885 prelude: :gerbil/base)\n")
    leaves = ["left", "right", "independent"] + [f"independent{i}" for i in range(cores - 2)]
    (fixture / "modules.scm").write_text("(" + " ".join(json.dumps(name) for name in ["join", *leaves]) + ")\n")
    for name in leaves:
        definitions = " ".join(f"(def (f{i} x) (bump x))" for i in range(64))
        (fixture / f"{name}.ss").write_text(
            "(import :std/iter :std/list/list) (export #t) "
            "(defrule (bump x) (foldl + x (for/collect (i (in-range 16)) i))) "
            + definitions + "\n")
    (fixture / "join.ss").write_text(
        "(import (prefix-in ./left l/) (prefix-in ./right r/)) "
        "(export answer) (def (answer x) (+ (l/f0 x) (r/f0 x)))\n")
    env = build_environment()
    for key in ("GERBIL_HOME", "GERBIL_LOADPATH", "GERBIL_GSC", "GAMBOPT"):
        env.pop(key, None)
    env.update(GERBIL_PATH=str(output / "gerbil-path"), D885_FIXTURE=str(fixture),
               GERBIL_GCC=env["GERBIL_GNU_GCC"], GERBIL_BUILD_CORES=str(cores))
    macros = subprocess.check_output([env["CC"], "-dM", "-E", "-x", "c", os.devnull], env=env, text=True)
    if "#define __clang__" in macros or "#define __GNUC__ 16\n" not in macros:
        raise RuntimeError("real GNU GCC 16 required")
    report = {"performanceQualified": False, "cores": cores, "runs": [],
              "hostLoadStart": os.getloadavg(), "logicalCpus": os.cpu_count(),
              "qualified": False, "fixtureSha256": {
                  p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in fixture.iterdir()}}
    report.update(strictProductProgress=args.strict_product_progress,
                  silenceBudgetSeconds=5 if args.strict_product_progress else 10,
                  wallBudgetSeconds=90 if args.strict_product_progress else 600)
    report["gerbilRef"] = subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"], text=True).strip()
    started = time.monotonic()
    command = [str(source / "run.sh"), "gxi"]
    if args.native_binary:
        home = source / "build"
        binary_home = args.binary_source.resolve() / "build" if args.binary_source else home
        if not binary_home.is_relative_to(repo / ".data"):
            parser.error("native binary must stay in project .data")
        overlay = args.library_overlay.resolve() if args.library_overlay else None
        if overlay and not overlay.is_relative_to(repo / ".data"):
            parser.error("library overlay must stay in project .data")
        env.pop("GERBIL_BUILD_PREFIX", None)
        env.update(GERBIL_HOME=str(home), GERBIL_GSC=str(home / "bin/gsc"),
                   GERBIL_LOADPATH=":".join(map(str, [output / "gerbil-path/lib", *([overlay] if overlay else []), home / "lib"])),
                   GAMBOPT=f"~~bin={home / 'bin'},~~lib={home / 'lib'},~~include={home / 'include'}",
                   PATH=f"{binary_home / 'bin'}:{home / 'bin'}:{env['PATH']}")
        command = [str(binary_home / "bin/gxi")]
        report["nativeBinary"] = True
        report["runtimeHome"] = str(home.relative_to(repo))
        report["binaryHome"] = str(binary_home.relative_to(repo))
        report["libraryOverlay"] = str(overlay.relative_to(repo)) if overlay else None
        report["toolchainBinarySha256"] = {
            name: hashlib.sha256((binary_home / "bin" / name).read_bytes()).hexdigest()
            for name in ("gxi", "gsc")}

    def save():
        (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")

    def run(name, argv):
        launch = time.monotonic()
        logfile = output / f"{name}.log"
        peak_gcc, activity, last_progress, ready = 0, "", launch, None
        events = {}
        with logfile.open("w") as log:
            process = subprocess.Popen(argv, env=env, cwd=fixture, stdout=subprocess.PIPE,
                                       stderr=subprocess.STDOUT, start_new_session=True, text=True)
            def collect():
                for line in process.stdout:
                    observed = time.monotonic()
                    gap = observed - events.get("last_output", launch)
                    events["maximumOutputGapSeconds"] = max(events.get("maximumOutputGapSeconds", 0), gap)
                    events["last_output"] = observed
                    log.write(line)
                    log.flush()
                    if "READY" in line and "ready" not in events:
                        events["ready"] = time.monotonic()
                events["end"] = time.monotonic()
            reader = Thread(target=collect, daemon=True)
            reader.start()
            try:
                previous_size = 0
                while process.poll() is None:
                    time.sleep(1)
                    content = logfile.read_text(errors="replace")
                    if ready is None and "READY" in content:
                        ready = time.monotonic() - launch
                    rows = [line.split(None, 3) for line in subprocess.check_output(
                        ["ps", "-axo", "pid,ppid,time,comm"], text=True).splitlines()[1:]]
                    descendants = {process.pid}
                    for _ in range(10):
                        descendants.update(int(row[0]) for row in rows if len(row) == 4 and int(row[1]) in descendants)
                    own = [row for row in rows if len(row) == 4 and int(row[0]) in descendants]
                    snapshot = repr(own)
                    peak_gcc = max(peak_gcc, sum(Path(row[3]).name == "cc1" for row in own))
                    if args.strict_product_progress:
                        last_progress = events.get("last_output", launch)
                    elif len(content) != previous_size or snapshot != activity:
                        last_progress = time.monotonic()
                    activity, previous_size = snapshot, len(content)
                    if int(time.monotonic() - launch) % 5 == 0:
                        print(f"PROGRESS {name}: {len(content)} log bytes; peak GCC frontends {peak_gcc}", flush=True)
                    if (time.monotonic() - last_progress > report["silenceBudgetSeconds"]
                            or time.monotonic() - launch > report["wallBudgetSeconds"]):
                        raise TimeoutError(f"{name}: exceeded product progress/batch gate")
                status = process.wait()
                reader.join(timeout=5)
            except BaseException:
                if process.poll() is None:
                    os.killpg(process.pid, signal.SIGTERM)
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        os.killpg(process.pid, signal.SIGKILL)
                        process.wait()
                raise
        content = logfile.read_text(errors="replace")
        if args.strict_product_progress and events.get("maximumOutputGapSeconds", 0) > 5:
            raise TimeoutError(f"{name}: recorded product output gap exceeds five seconds")
        if status or "*** ERROR" in content:
            raise RuntimeError(f"{name} failed: {logfile.name}")
        if ready is None and "READY" not in content:
            raise RuntimeError(f"{name} did not reach readiness")
        row = {"name": name, "launchSeconds": launch - started,
               "endSeconds": events["end"] - started, "wallSeconds": events["end"] - launch,
               "readySeconds": events["ready"] - launch,
               "maximumOutputGapSeconds": events.get("maximumOutputGapSeconds", 0),
               "peakConcurrentGccFrontends": peak_gcc, "log": logfile.name}
        print(f"OK {name}: {row['wallSeconds']:.3f}s", flush=True)
        return row

    try:
        for label, expression in (
            ("runtime", '(displayln "READY runtime")'),
            ("make-test-import", '(begin (eval \'(import :std/make :std/test)) (displayln "READY imports"))')):
            for repeat in range(args.repeats):
                with ThreadPoolExecutor(max_workers=cores) as pool:
                    futures = [pool.submit(run, f"{label}-{repeat}-{index}", command + ["-e", expression]) for index in range(cores)]
                    pair = [future.result() for future in futures]
                overlap = min(row["endSeconds"] for row in pair) - max(row["launchSeconds"] for row in pair)
                if overlap <= 0:
                    raise RuntimeError("startup processes did not overlap")
                for row in pair:
                    row["pairOverlapSeconds"] = overlap
                report["runs"].extend(pair)
                save()
        script = Path(__file__).with_name("concurrent-make-test.ss")
        row = run("parallel-make", command + [str(script)])
        content = (output / row["log"]).read_text()
        if "(D885-OK)" not in content or content.count("CASE-OK") != 3:
            raise RuntimeError("all three std/test cases must pass")
        row["phases"] = dict((name, float(seconds)) for name, seconds in re.findall(
            r"\(PHASE-END (\S+) ([0-9.eE+-]+)\)", content))
        report["runs"].append(row)
        report["qualified"] = True
        report["nativeConcurrencyObserved"] = row["peakConcurrentGccFrontends"] >= 2
        report["fullHardwareConcurrencyObserved"] = row["peakConcurrentGccFrontends"] >= cores
    except BaseException as error:
        report["failure"] = str(error)
        raise
    finally:
        report["hostLoadEnd"] = os.getloadavg()
        save()


if __name__ == "__main__":
    main()
