#!/usr/bin/env python3
"""Bounded native correctness gate for the isolated Darwin host prototype."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time

from bazel_host_environment import build_environment


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    output = args.output.resolve()
    if not output.is_relative_to(root / ".data"):
        parser.error("output must be under project .data")
    output.mkdir(parents=True, exist_ok=False)
    env = build_environment()
    cores = int(subprocess.check_output(["sysctl", "-n", "hw.physicalcpu"], text=True))
    env["GERBIL_BUILD_CORES"] = str(cores)
    env.pop("GAMBIT_HOST_GROUP_BUDGET", None)
    macros = subprocess.check_output([env["CC"], "-dM", "-E", "-x", "c", os.devnull], env=env, text=True)
    if "#define __GNUC__ 16\n" not in macros or "#define __clang__" in macros:
        raise RuntimeError("real GNU GCC 16 required")
    report = {"qualified": False, "performanceQualified": False, "cores": cores,
              "hostLoad": os.getloadavg(), "steps": []}

    def save():
        (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")

    def run(name, command, environment):
        print(f"START {name}", flush=True)
        log = output / f"{name}.log"
        start = time.monotonic()
        with log.open("w") as stream:
            child = subprocess.Popen(command, env=environment, stdout=stream,
                                     stderr=subprocess.STDOUT, start_new_session=True)
            previous, progress = None, start
            try:
                while child.poll() is None:
                    time.sleep(2)
                    rows = subprocess.check_output(["ps", "-axo", "pid,ppid,time,comm"], text=True).splitlines()[1:]
                    rows = [row.split(None, 3) for row in rows]
                    family = {child.pid}
                    for _ in range(8):
                        family.update(int(row[0]) for row in rows if len(row) == 4 and int(row[1]) in family)
                    activity = [row for row in rows if len(row) == 4 and int(row[0]) in family]
                    state = (log.stat().st_size, activity)
                    now = time.monotonic()
                    if state != previous:
                        progress = now
                    previous = state
                    print(f"PROGRESS {name}: bytes={state[0]} children={activity}", flush=True)
                    if child.poll() is None and (now - progress > 10 or now - start > 180):
                        raise TimeoutError(f"{name}: progress/180-second gate")
                status = child.wait()
            except BaseException:
                if child.poll() is None:
                    os.killpg(child.pid, signal.SIGTERM)
                    try:
                        child.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        os.killpg(child.pid, signal.SIGKILL)
                        child.wait()
                raise
        contents = log.read_text(errors="replace")
        passed = status == 0 and "*** ERROR" not in contents
        report["steps"].append({"name": name, "exitCode": status, "passed": passed,
                                "wallSeconds": time.monotonic() - start, "log": log.name})
        save()
        if not passed:
            raise RuntimeError(f"{name} failed; see {log.name}")
        print(f"OK {name}", flush=True)
        return contents

    def compiler(source):
        gambit = source.resolve() / "src/gambit"
        return [str(gambit / "gsc/gsc"),
                f"-:~~bin={gambit / 'bin'},~~lib={gambit / 'lib'},~~include={gambit / 'include'}"]

    try:
        save()
        host_source = args.candidate.resolve() / "src/gambit/gsc/_host.scm"
        expression = ('(call-with-input-file ' + json.dumps(str(host_source)) +
                      " (lambda (p) (let loop () (let ((x (read p))) "
                      "(cond ((eof-object? x) (error \"missing platform predicate\")) "
                      "((and (pair? x) (eq? (car x) 'define) "
                      "(eq? (cadr x) 'host-darwin-gnu-gcc?)) "
                      "(display (cadddr (caddr x)))) (else (loop)))))))")
        guard = subprocess.check_output(compiler(args.baseline) + ["-e", expression], env=env, text=True)
        probe = output / "platform-guard.c"
        probe.write_text("#define ___result result\nint main(void) { int result = 99;\n" +
                         guard + "\nreturn result != EXPECTED;\n}\n")
        for name, flags, expected in (("darwin-gcc", [], 1),
                                     ("non-darwin", ["-U__APPLE__", "-U__MACH__"], 0),
                                     ("clang-excluded", ["-D__clang__=1"], 0)):
            executable = output / (name + "-guard")
            run(name + "-guard-build", [env["CC"], *flags, f"-DEXPECTED={expected}",
                                       str(probe), "-o", str(executable)], env)
            run(name + "-guard-execute", [str(executable)], env)
        report["platformGuardBranchesPassed"] = True
        generated = {}
        for name, source, budget in (("baseline", args.baseline, None),
                                     ("candidate-off", args.candidate, None),
                                     ("candidate-8", args.candidate, 8),
                                     ("candidate-64", args.candidate, 64),
                                     ("candidate-256", args.candidate, 256)):
            directory = output / name
            directory.mkdir()
            e = dict(env)
            if budget is not None:
                e["GAMBIT_HOST_GROUP_BUDGET"] = str(budget)
            cfile = directory / "contract.c"
            run(name + "-generate", compiler(source) + ["-c", "-o", str(cfile), str(args.fixture.resolve())], e)
            generated[name] = cfile.read_bytes()
            if budget is not None and b"#undef ___GH_PROC" not in generated[name]:
                raise RuntimeError(f"{name}: grouping was not exercised")
            executable = directory / "contract"
            run(name + "-native", compiler(source) + ["-exe", "-o", str(executable), str(cfile)], e)
            results = run(name + "-execute", [str(executable)], e)
            if results.count("CASE-OK") != 11 or not results.rstrip().endswith("HARNESS-OK\nOK"):
                raise RuntimeError(f"{name}: incomplete semantic gate")
        report["disabledCByteIdentical"] = generated["baseline"] == generated["candidate-off"]
        report["baselineCsha256"] = hashlib.sha256(generated["baseline"]).hexdigest()
        if not report["disabledCByteIdentical"]:
            raise RuntimeError("disabled prototype changed generated C")
        report["qualified"] = True
        save()
    except BaseException as error:
        report["failure"] = str(error)
        save()
        raise


if __name__ == "__main__":
    main()
