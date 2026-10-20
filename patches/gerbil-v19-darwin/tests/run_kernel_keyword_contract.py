#!/usr/bin/env python3
"""Load one original-GSC native keyword fixture with baseline and candidate VMs."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
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
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--fixture", type=Path)
    parser.add_argument("--marker", default="KEYWORD-OUTLINE-OK 1512")
    parser.add_argument("--fixture-include-dir", type=Path)
    parser.add_argument("--gsc-hook", type=Path)
    parser.add_argument("--structure-helper-only", action="store_true")
    parser.add_argument("--fixture-dynamic-lookup", action="store_true")
    parser.add_argument("--compiler-source", type=Path)
    parser.add_argument("--native-structure-jump", action="store_true")
    parser.add_argument("--native-structure-expression", action="store_true")
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[3]
    output = args.output.resolve()
    if not output.is_relative_to(repo / ".data"):
        parser.error("receipts must stay under project .data")
    output.mkdir(parents=True, exist_ok=False)
    home = args.baseline.resolve() / "build"
    candidate = args.candidate.resolve() / "build"
    compiler = args.compiler_source.resolve() / "build/bin/gsc" if args.compiler_source else home / "bin/gsc"
    if not compiler.is_relative_to(repo / ".data"):
        parser.error("native fixture compiler must be project-local")
    fixture = args.fixture.resolve() if args.fixture else Path(__file__).with_name("gambit-keyword-outline-contract.scm")
    if not fixture.is_relative_to(repo):
        parser.error("native fixture must be project-local")
    env = build_environment()
    env.update(GERBIL_HOME=str(home), GERBIL_PATH=str(output / "empty-user"),
               GERBIL_LOADPATH=str(home / "lib"), GERBIL_GSC=str(home / "bin/gsc"),
               GAMBOPT=f"~~bin={home / 'bin'},~~lib={home / 'lib'},~~include={home / 'include'}")
    report = {"qualified": False, "performanceQualified": False, "cores": os.cpu_count(),
              "compilerSha256": hashlib.sha256(compiler.read_bytes()).hexdigest(),
              "fixtureSha256": hashlib.sha256(fixture.read_bytes()).hexdigest(), "runs": []}

    def invoke(name, command):
        started = time.monotonic()
        with (output / f"{name}.log").open("w") as log:
            child = subprocess.Popen(command, env=env, stdout=log, stderr=subprocess.STDOUT,
                                     start_new_session=True)
            try:
                code = child.wait(timeout=120)
            except subprocess.TimeoutExpired:
                os.killpg(child.pid, signal.SIGTERM)
                try:
                    child.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(child.pid, signal.SIGKILL)
                    child.wait()
                raise
        text = (output / f"{name}.log").read_text(errors="replace")
        if code or "*** ERROR" in text or (name != "compile-fixture" and args.marker not in text):
            raise RuntimeError(f"{name} failed; inspect retained log")
        print(f"OK {name}: {time.monotonic() - started:.3f}s", flush=True)
        return {"name": name, "exitCode": code, "wallSeconds": time.monotonic() - started}

    try:
        native = output / "keyword-contract.o1"
        local_fixture = output / "native-fixture.scm"
        local_fixture.write_bytes(fixture.read_bytes())
        compile_args = [str(compiler), "-dynamic", "-keep-temp", "-o", str(native)]
        if args.fixture_dynamic_lookup:
            compile_args += ["-ld-options", "-undefined dynamic_lookup"]
        cc_options = []
        if args.native_structure_jump:
            cc_options.append(f'-include {Path(__file__).with_name("gambit-structure-native-jump.h")}')
        if args.native_structure_expression:
            cc_options.append(f'-include {Path(__file__).with_name("gambit-structure-native-expression.h")}')
        if args.fixture_include_dir:
            include = args.fixture_include_dir.resolve()
            if not include.is_relative_to(repo):
                parser.error("fixture include path must be project-local")
            cc_options.append(f"-I{include}")
        if args.structure_helper_only:
            cc_options.append("-DGB_STRUCTURE_HELPER_ONLY")
        if cc_options:
            compile_args += ["-cc-options", " ".join(cc_options)]
        if args.gsc_hook:
            hook = args.gsc_hook.resolve()
            if not hook.is_relative_to(repo):
                parser.error("compiler hook must be project-local")
            snapshot = output / "compiler-hook.scm"
            snapshot.write_bytes(hook.read_bytes())
            report["compilerHookSha256"] = hashlib.sha256(snapshot.read_bytes()).hexdigest()
            compile_args += ["-e", f"(load {json.dumps(str(snapshot))})"]
        report["runs"].append(invoke("compile-fixture", [*compile_args, str(local_fixture)]))
        report["nativeFixtureSha256"] = hashlib.sha256(native.read_bytes()).hexdigest()
        expression = f"(load {json.dumps(str(native))})"
        report["runs"].append(invoke("baseline", [str(home / "bin/gxi"), "-e", expression]))
        with ThreadPoolExecutor(max_workers=report["cores"]) as pool:
            futures = [pool.submit(invoke, f"candidate-{index}",
                                   [str(candidate / "bin/gxi"), "-e", expression])
                       for index in range(report["cores"])]
            for future in as_completed(futures):
                report["runs"].append(future.result())
        report["qualified"] = True
    except BaseException as error:
        report["failure"] = str(error)
        raise
    finally:
        (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
