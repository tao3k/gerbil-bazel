#!/usr/bin/env python3
"""Qualify the rebuilt GSC emitter on the unchanged real MCP embedded module."""
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
    for name in ("baseline", "candidate", "project", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[3]
    baseline, candidate, project, output = (
        getattr(args, n).resolve() for n in ("baseline", "candidate", "project", "output"))
    if not all(p.is_relative_to(repo / ".data") for p in (baseline, candidate, project, output)):
        parser.error("all paths must remain in project .data")
    output.mkdir(exist_ok=False)
    home = baseline / "build"
    env = build_environment()
    env.update(GERBIL_HOME=str(home), GERBIL_PATH=str(output / "user"),
               GERBIL_LOADPATH=str(home / "lib"), GERBIL_BUILD_CORES=str(os.cpu_count()),
               GAMBOPT=f"~~bin={home / 'bin'},~~lib={home / 'lib'},~~include={home / 'include'}")
    report = {"qualified": False, "performanceQualified": False, "commands": [], "objects": []}

    def run(name, command):
        started = time.monotonic()
        with (output / f"{name}.log").open("w") as log:
            child = subprocess.Popen(command, cwd=project, env=env, stdout=log,
                                     stderr=subprocess.STDOUT, start_new_session=True)
            try:
                code = child.wait(timeout=180)
            except subprocess.TimeoutExpired:
                os.killpg(child.pid, signal.SIGTERM)
                try:
                    child.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(child.pid, signal.SIGKILL)
                    child.wait()
                raise
        elapsed = time.monotonic() - started
        report["commands"].append({"name": name, "exitCode": code, "wallSeconds": elapsed})
        if code or "*** ERROR" in (output / f"{name}.log").read_text(errors="replace"):
            raise RuntimeError(f"{name} failed; inspect durable log")
        print(f"OK {name}: {elapsed:.3f}s (functional qualification, not timing admission)", flush=True)

    try:
        scheme = output / "scheme"
        scheme.mkdir()
        run("gerbil-emit-real-module", [str(home / "bin/gxc"), "-O", "-S", "-d", str(scheme),
                                        str(project / "data/embedded.ss")])
        scm = max(scheme.rglob("*.scm"), key=lambda p: p.stat().st_size)
        report["schemeSha256"] = hashlib.sha256(scm.read_bytes()).hexdigest()
        compilers = {"original": home / "bin/gsc", "packed": candidate / "src/gambit/gsc/gsc"}
        report["compilerSha256"] = {n: hashlib.sha256(p.read_bytes()).hexdigest()
                                    for n, p in compilers.items()}
        for name, compiler in compilers.items():
            arm = output / name
            arm.mkdir()
            c = arm / "embedded.c"
            obj = arm / "embedded.o"
            run(name + "-emit", [str(compiler), "-c", "-o", str(c), str(scm)])
            has_packed = "#if defined(__APPLE__) && defined(__GNUC__)" in c.read_text()
            if has_packed != (name == "packed"):
                raise RuntimeError("rebuilt compiler did not select expected emitter")
            run(name + "-object", [str(home / "bin/gsc"), "-obj", "-cc-options", "-D___DYNAMIC -fPIC",
                                    "-o", str(obj), str(c)])
            report["objects"].append({"variant": name, "cBytes": c.stat().st_size,
                                      "sha256": hashlib.sha256(obj.read_bytes()).hexdigest()})
        report["qualified"] = len({r["sha256"] for r in report["objects"]}) == 1
        if not report["qualified"]:
            raise RuntimeError("real module native objects differ")
        print("REAL-MCP-PACKED-EMITTER-OBJECT-EQUIVALENCE-OK", flush=True)
    finally:
        (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
