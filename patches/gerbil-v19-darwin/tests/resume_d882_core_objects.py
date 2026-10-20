#!/usr/bin/env python3
"""Resume native stage1 jobs without regenerating retained Scheme inputs."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument("source", type=Path)
parser.add_argument("output", type=Path)
args = parser.parse_args()
source = args.source.resolve()
output = args.output.resolve()
output.mkdir(parents=True, exist_ok=False)
build = source / "build"
environment = dict(os.environ)
for key in ("SDKROOT", "CPATH", "C_INCLUDE_PATH", "CPLUS_INCLUDE_PATH", "LIBRARY_PATH"):
    environment.pop(key, None)
environment["COMPILER_PATH"] = "/usr/bin"
inputs = sorted((build / "lib/gerbil").rglob("*.scm"))
if not inputs:
    raise RuntimeError("No retained stage1 Scheme inputs")
report = {"inputs": {}, "skipped": [], "compiled": []}
pending = []
for path in inputs:
    relative = str(path.relative_to(build))
    report["inputs"][relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    artifact = path.with_suffix(".o1")
    reusable = artifact.exists() and artifact.stat().st_mtime_ns >= path.stat().st_mtime_ns
    if reusable:
        # Verify load commands before considering an interrupted linker output.
        reusable = subprocess.run(["otool", "-L", str(artifact)],
                                  stdout=subprocess.DEVNULL,
                                  stderr=subprocess.DEVNULL).returncode == 0
    if reusable:
        report["skipped"].append(relative)
    else:
        pending.append(path)
print(f"D882-CORE-RESUME inputs={len(inputs)} reused={len(report['skipped'])} pending={len(pending)}", flush=True)

def compile_one(path):
    relative = str(path.relative_to(build))
    print(f"D882-COMPILE-BEGIN {relative}", flush=True)
    log = output / (relative.replace("/", "_") + ".log")
    with log.open("w") as handle:
        process = subprocess.Popen(
            [str(build / "bin/gsc"), f"-:~~={build}", "-e",
             '(include "~~lib/_gambit#.scm")', str(path)],
            cwd=source / "src", env=environment, stdout=handle,
            stderr=subprocess.STDOUT, start_new_session=True)
        try:
            result = process.wait(timeout=1800)
        except BaseException:
            os.killpg(process.pid, signal.SIGTERM)
            process.wait()
            raise
    if result:
        raise RuntimeError(f"Native compilation failed: {relative}; see {log.name}")
    artifact = path.with_suffix(".o1")
    if not artifact.exists() or artifact.stat().st_size == 0:
        raise RuntimeError(f"Missing native artifact: {relative}")
    print(f"D882-COMPILE-OK {relative}", flush=True)
    return relative

try:
    with ThreadPoolExecutor(max_workers=2) as pool:
        for result in pool.map(compile_one, pending):
            report["compiled"].append(result)
finally:
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
print("D882-CORE-NATIVE-JOBS-OK", flush=True)
