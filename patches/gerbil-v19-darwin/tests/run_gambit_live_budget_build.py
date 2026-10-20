#!/usr/bin/env python3
"""Build latest-source base libraries/tests with an isolated evaluator hook."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import shutil
import subprocess
import time
from bazel_host_environment import build_environment

parser = argparse.ArgumentParser()
parser.add_argument("--source", type=Path, required=True)
parser.add_argument("--toolchain", type=Path, required=True)
parser.add_argument("--output", type=Path, required=True)
parser.add_argument("--gcc", default=shutil.which("gcc-16"))
parser.add_argument("--native-tests", action="store_true",
                    help="Extra AOT test check; default uses upstream gxtest source tests")
args = parser.parse_args()
if not args.gcc:
    parser.error("GNU GCC 16 is required; provide --gcc")
args.source = args.source.resolve()
args.toolchain = args.toolchain.resolve()
args.output = args.output.resolve()
args.gcc = shutil.which(args.gcc) or str(Path(args.gcc).resolve())
here = Path(__file__).resolve().parent
args.output.mkdir(parents=True, exist_ok=False)
fixture = args.output / "fixture"
fixture.mkdir()
gsc_home = args.output / "gsc-home"
gsc_home.mkdir()
(gsc_home / ".gambini").write_text('(load (getenv "D881_HOOK"))\n')
files = {
    "list-builder": "list/list-builder.ss",
    "list": "list/list.ss", "list-test": "list/list-test.ss",
    "vector": "vector/vector.ss", "vector-test": "vector/vector-test.ss",
    "values": "values.ss", "values-test": "values-test.ss",
    "func": "func.ss",
    "iter/interface": "iter/interface.ss",
    "iter/iterators": "iter/iterators.ss",
    "iter/macros": "iter/macros.ss",
    "iter/api": "iter/api.ss", "iter": "iter.ss",
    "iter/iter-test": "iter/iter-test.ss",
}
source_receipts = {}
for name, relative in files.items():
    source = args.source / "src/std" / relative
    data = source.read_text()
    source_receipts[relative] = hashlib.sha256(source.read_bytes()).hexdigest()
    if name == "list-test":
        data = data.replace(":std/list/list\n", "./list\n")
    if name == "values-test":
        data = data.replace(":std/values)", "./values)")
    if name == "iter/macros":
        data = data.replace(":std/list/list-builder\n",
                            ":d881-fixture/list-builder\n")
    if name == "iter/iter-test":
        data = data.replace(":std/iter)", ":d881-fixture/iter)")
    target = fixture / f"{name}.ss"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(data)
(fixture / "gerbil.pkg").write_text("(package: d881-fixture prelude: :gerbil/base)\n")
spec = " ".join(
    f'(gxc: \"{name}\" \"-keep-temp\" \"-cc-options\" \"-ftrack-macro-expansion=0\")'
    for name in files if args.native_tests or not name.endswith("-test")
)
(fixture / "build.ss").write_text(
    '(import :std/build-script)\n'
    f"(defbuild-script '({spec}) parallelize: #f optimize: #t verbose: 2)\n"
)
(fixture / "test.ss").write_text(
    '(import :std/test/base :d881-fixture/list-test '
    ':d881-fixture/vector-test :d881-fixture/values-test '
    ':d881-fixture/iter/iter-test)\n'
    '(parameterize ((current-test-config (TestConfig verbosity: 5 capture-output?: #f)))\n'
    '  (let ((results (map (lambda (suite) (test-result-ok? (test-suite! suite)))\n'
    '                      [list-test vector-test values-test iter-test])))\n'
    '    (unless (andmap (lambda (result) result) results)\n'
    '      (error "D881 upstream suite failed"))))\n'
    '(display "D881-REAL-LIBRARY-TESTS-OK\\n")\n'
)
environment = build_environment()
for key in ("GERBIL_HOME", "GERBIL_LOADPATH"):
    environment.pop(key, None)
environment.update({
    "COMPILER_PATH": "/usr/bin", "CC": args.gcc, "GERBIL_CC": args.gcc,
    "GERBIL_GCC": args.gcc,
    "GERBIL_GSC": str(here / "gambit-live-budget-gsc.sh"),
    "D881_GSC_REAL": str(args.toolchain / "bin/gsc"),
    "D881_TOOLCHAIN_HOME": str(args.toolchain),
    "D881_HOOK": str(here / "gambit-live-budget-build-hook.scm"),
    "D881_GSC_HOME": str(gsc_home),
})
gcc_macros = subprocess.check_output(
    [args.gcc, "-dM", "-E", "-x", "c", os.devnull],
    env=environment, text=True, timeout=30)
if "#define __clang__" in gcc_macros or not re.search(
        r"^#define __GNUC__ 16$", gcc_macros, re.MULTILINE):
    raise RuntimeError("Real GNU GCC 16 is required; rejecting this compiler")
(args.output / "gcc-predefined-macros.log").write_text(gcc_macros)
hook = args.output / "build-hook.o1"
hook_command = [str(args.toolchain / "bin/gsc"), f"-:~~={args.toolchain}",
                "-f", "-dynamic", "-cc-options", "-ftrack-macro-expansion=0",
                "-o", str(hook), str(here / "gambit-live-budget-build-hook.scm")]
with (args.output / "hook-build.log").open("w") as log:
    subprocess.run(hook_command, env=environment, stdout=log,
                   stderr=subprocess.STDOUT, check=True, timeout=120)
environment["D881_HOOK"] = str(hook)
gxi = str(args.toolchain / "bin/gxi")
gxi_command = [gxi, f"-:~~={args.toolchain}"]
report = {"source": str(args.source), "toolchain": str(args.toolchain),
          "sourceSha256": source_receipts, "runs": [], "timingQualified": False,
          "qualification": "Host load and instrumented hook: exploratory only"}
report["testFlow"] = "extra-native-tests" if args.native_tests else "upstream-gxtest-source"
host_discovery = here.parents[2] / "gerbil/host_system.bzl"
report["bazelHostDiscoverySha256"] = hashlib.sha256(host_discovery.read_bytes()).hexdigest()
report["buildEnvironment"] = {key: environment[key] for key in
    ("CC", "CXX", "SDKROOT", "DEVELOPER_DIR", "CPATH", "LIBRARY_PATH",
     "LDFLAGS", "PKG_CONFIG_PATH", "GERBIL_BUILD_CORES") if key in environment}
report["gerbilHead"] = subprocess.check_output(
    ["git", "-C", str(args.source), "rev-parse", "HEAD"], text=True).strip()
report["gambitHead"] = subprocess.check_output(
    ["git", "-C", str(args.source / "src/gambit"), "rev-parse", "HEAD"],
    text=True).strip()
report["gccVersion"] = subprocess.check_output(
    [environment["GERBIL_GCC"], "--version"], text=True).splitlines()[0]
report["gscVersion"] = subprocess.check_output(
    [str(args.toolchain / "bin/gsc"), f"-:~~={args.toolchain}", "-v"],
    env=environment, text=True)
try:
    for mode in ("baseline", "candidate"):
        root = args.output / mode
        root.mkdir()
        env = dict(environment, GERBIL_PATH=str(root), D881_MODE=mode)
        row = {"mode": mode, "loadStart": os.getloadavg()}
        test_command = (gxi_command + ["test.ss"] if args.native_tests else
            gxi_command + [":gerbil/tools/gxtest", "-v", "5",
                           "list-test.ss", "vector-test.ss", "values-test.ss",
                           "iter/iter-test.ss"])
        for phase, command in (
            ("build", gxi_command + ["build.ss", "compile"]),
            ("test", test_command),
        ):
            start = time.monotonic()
            log_path = args.output / f"{mode}-{phase}.log"
            with log_path.open("w") as output:
                process = subprocess.Popen(command, cwd=fixture, env=env,
                                           stdout=output, stderr=subprocess.STDOUT,
                                           start_new_session=True)
                seen = 0
                try:
                    while process.poll() is None:
                        time.sleep(2)
                        progress = log_path.read_text()
                        if len(progress) > seen:
                            print(progress[seen:], end="", flush=True)
                            seen = len(progress)
                        if time.monotonic() - start > 1800:
                            raise TimeoutError(f"{mode} {phase} exceeded 1800 seconds")
                except BaseException:
                    os.killpg(process.pid, signal.SIGTERM)
                    process.wait()
                    raise
            log = log_path.read_text()
            print(log[seen:], end="", flush=True)
            row[phase] = {"seconds": time.monotonic() - start,
                          "exitCode": process.returncode}
            if phase == "test":
                marker = ("D881-REAL-LIBRARY-TESTS-OK" if args.native_tests else "OK")
                row[phase]["completionMarker"] = bool(log.strip()) and log.strip().splitlines()[-1] == marker
                row[phase]["passed"] = process.returncode == 0 and row[phase]["completionMarker"]
            if phase == "build":
                row["gvmStats"] = re.findall(
                    r'D881-STATS \("[^\"]+" (\d+) (\d+) (\d+) (\d+)\)', log)
            if process.returncode and phase == "build":
                report["runs"].append(row)
                raise RuntimeError(f"{mode} {phase} failed; see saved log")
        row["cSha256"] = {
            str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(root.rglob("*.c"))
        }
        row["nativeArtifacts"] = sum(
            path.is_file() and bool(re.fullmatch(r"\.o\d+", path.suffix))
            for path in root.rglob("*.o*"))
        if not row["gvmStats"] or not sum(int(s[0]) for s in row["gvmStats"]):
            raise RuntimeError("GVM hook was not exercised; discard this run")
        if not row["cSha256"] or not row["nativeArtifacts"]:
            raise RuntimeError("Missing generated C or native artifacts")
        row["loadEnd"] = os.getloadavg()
        report["runs"].append(row)
        print(json.dumps(row), flush=True)
    baseline, candidate = report["runs"]
    report["identicalGeneratedC"] = baseline["cSha256"] == candidate["cSha256"]
    report["candidateStatsTotals"] = [
        sum(int(row[i]) for row in candidate["gvmStats"]) for i in range(4)
    ]
    report["allTestsPassed"] = all(row["test"]["passed"]
                                   for row in report["runs"])
    if not report["allTestsPassed"]:
        raise RuntimeError("Upstream tests failed; both mode logs retained")
finally:
    (args.output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
