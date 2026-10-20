#!/usr/bin/env python3
"""Retest retained native libraries with the official tool module, without rebuild."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time
from bazel_host_environment import build_environment

parser = argparse.ArgumentParser()
parser.add_argument("output", type=Path)
args = parser.parse_args()
output = args.output.resolve()
report_path = output / "report.json"
report = json.loads(report_path.read_text())
source = Path(report["source"])
toolchain = Path(report["toolchain"])
for key, checkout in (("gerbilHead", source), ("gambitHead", source / "src/gambit")):
    head = subprocess.check_output(["git", "-C", str(checkout), "rev-parse", "HEAD"], text=True).strip()
    if head != report[key]:
        raise RuntimeError(f"Changed source head: {key}")
for relative, digest in report["sourceSha256"].items():
    if hashlib.sha256((source / "src/std" / relative).read_bytes()).hexdigest() != digest:
        raise RuntimeError(f"Changed library source: {relative}")
environment = build_environment()
for key in ("GERBIL_HOME", "GERBIL_LOADPATH"):
    environment.pop(key, None)
for row in report["runs"]:
    mode = row["mode"]
    root = output / mode
    for relative, digest in row["cSha256"].items():
        if hashlib.sha256((root / relative).read_bytes()).hexdigest() != digest:
            raise RuntimeError(f"Changed generated C: {mode}/{relative}")
    env = dict(environment, GERBIL_PATH=str(root))
    command = [str(toolchain / "bin/gxi"), f"-:~~={toolchain}",
               ":gerbil/tools/gxtest", "-v", "5", "list-test.ss", "vector-test.ss",
               "values-test.ss", "iter/iter-test.ss"]
    log_path = output / f"{mode}-test-official.log"
    start = time.monotonic()
    seen = 0
    with log_path.open("w") as log:
        process = subprocess.Popen(command, cwd=output / "fixture", env=env,
                                   stdout=log, stderr=subprocess.STDOUT,
                                   start_new_session=True)
        try:
            while process.poll() is None:
                time.sleep(2)
                progress = log_path.read_text()
                print(progress[seen:], end="", flush=True)
                seen = len(progress)
                if time.monotonic() - start > 1800:
                    raise TimeoutError(f"{mode} official tests timed out")
        except BaseException:
            os.killpg(process.pid, signal.SIGTERM)
            process.wait()
            raise
    log = log_path.read_text()
    print(log[seen:], end="", flush=True)
    marker = bool(log.strip()) and log.strip().splitlines()[-1] == "OK"
    row["discardedTestEntry"] = row["test"]
    row["test"] = {"seconds": time.monotonic() - start, "exitCode": process.returncode,
                   "completionMarker": marker, "passed": process.returncode == 0 and marker,
                   "log": log_path.name}
    print(json.dumps({"mode": mode, "test": row["test"]}), flush=True)
report["testFlow"] = "upstream-gxtest-module-source"
report["allTestsPassed"] = all(row["test"]["passed"] for row in report["runs"])
report_path.write_text(json.dumps(report, indent=2) + "\n")
if not report["allTestsPassed"]:
    raise RuntimeError("Official upstream tests failed; no native library rebuild was performed")
