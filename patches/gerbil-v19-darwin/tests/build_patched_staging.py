#!/usr/bin/env python3
"""Qualify the audited patches in a fresh checkout under project .data."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import shlex
import shutil
import subprocess
import time
from bazel_host_environment import build_environment


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-cache", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--gerbil-ref", required=True)
    parser.add_argument("--gambit-ref", required=True)
    parser.add_argument("--prepared-source", type=Path)
    parser.add_argument("--continue-gambit-wip", action="store_true")
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    if args.continue_gambit_wip and not (args.resume and args.prepared_source):
        parser.error("WIP continuation requires a prepared source resume")
    repository = Path(__file__).resolve().parents[3]
    output = args.output.resolve()
    if not output.is_relative_to(repository / ".data"):
        parser.error("output must be inside this project's .data")
    output.mkdir(parents=True, exist_ok=args.resume)
    cache = args.source_cache.resolve()
    source = args.prepared_source.resolve() if args.prepared_source else output / "source"
    if args.prepared_source and (not source.is_relative_to(repository / ".data") or source == cache):
        parser.error("prepared source must be an isolated project .data checkout")
    env = build_environment()
    for key in ("GERBIL_HOME", "GERBIL_LOADPATH", "GERBIL_GSC", "GAMBOPT"):
        env.pop(key, None)
    env["GERBIL_PATH"] = str(output / "gerbil-path")
    env["GERBIL_GCC"] = env["GERBIL_GNU_GCC"]
    env["CFLAGS"] = env.get("CFLAGS", "") + " -pipe"
    cores = int(subprocess.check_output(["/usr/sbin/sysctl", "-n", "hw.physicalcpu"], text=True))
    env["GERBIL_BUILD_CORES"] = str(cores)
    report = {"gerbilRef": args.gerbil_ref, "gambitRef": args.gambit_ref,
              "cores": cores, "performanceQualified": False, "qualified": False,
              "steps": [], "patches": []}
    if args.resume:
        report = json.loads((output / "report.json").read_text())
        if (report["gerbilRef"], report["gambitRef"]) != (args.gerbil_ref, args.gambit_ref):
            parser.error("resume source identities differ")
        report.pop("failure", None)
        report["qualified"] = False
        report["cores"] = cores

    def save():
        (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")

    def run(name, command, cwd=repository):
        previous_steps = [step for step in report["steps"] if step["name"] == name]
        if args.resume and previous_steps and previous_steps[-1].get("passed", previous_steps[-1]["exitCode"] == 0):
            print(f"REUSE completed step {name}", flush=True)
            return
        print(f"START {name}", flush=True)
        log = output / f"{name}.log"
        started = time.monotonic()
        with log.open("w") as stream:
            process = subprocess.Popen(command, cwd=cwd, env=env, stdout=stream,
                                       stderr=subprocess.STDOUT, start_new_session=True)
            position, last_progress, previous = 0, started, ""
            descendants = {process.pid}
            try:
                while process.poll() is None:
                    time.sleep(5)
                    with log.open() as reader:
                        reader.seek(position)
                        new = reader.read()
                        position = reader.tell()
                    try:
                        snapshot = subprocess.check_output(["/bin/ps", "-axo", "pid,ppid"], text=True, timeout=3)
                        parents = [row.split() for row in snapshot.splitlines()[1:]]
                        descendants = {process.pid}
                        for _ in range(8):
                            descendants.update(int(row[0]) for row in parents if len(row) == 2 and int(row[1]) in descendants)
                    except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
                        pass
                    observed = True
                    try:
                        snapshot = subprocess.check_output(["/bin/ps", "-p", ",".join(map(str, sorted(descendants))),
                            "-o", "pid,ppid,pgid,time,comm"], text=True, timeout=3)
                        rows = [row.split(None, 4) for row in snapshot.splitlines()[1:]]
                        activity = " | ".join(" ".join(row) for row in rows
                                              if len(row) == 5 and int(row[2]) == process.pid)
                    except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
                        observed = False
                        activity = "observer unavailable (not counted as progress)"
                    if new or (observed and activity != previous):
                        last_progress = time.monotonic()
                    if observed:
                        previous = activity
                    print(f"PROGRESS {name}: " + (" | ".join(new.splitlines()[-2:]) if new else activity), flush=True)
                    if observed and process.poll() is None and time.monotonic() - last_progress >= 10:
                        raise TimeoutError(f"{name}: no log or child CPU progress for ten seconds")
                    if time.monotonic() - started > 7200:
                        raise TimeoutError(f"{name} exceeded two hours")
                status = process.wait()
            except BaseException:
                if process.poll() is None:
                    os.killpg(process.pid, signal.SIGTERM)
                    try:
                        process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        os.killpg(process.pid, signal.SIGKILL)
                        process.wait()
                raise
        passed = status == 0 and not any(marker in log.read_text(errors="replace").lower()
                                        for marker in ("heap overflow", "*** error", "compilation error;"))
        report["steps"].append({"name": name, "exitCode": status, "passed": passed,
                                "wallSeconds": round(time.monotonic() - started, 3), "log": log.name})
        save()
        if not passed:
            raise RuntimeError(f"{name} failed; inspect {log.name}")
        print(f"OK {name}", flush=True)

    def check_sources(label):
        for index, filename in enumerate(("src/gerbil/compiler/base.ss", "src/gerbil/compiler/driver.ss")):
            path = source / filename
            expression = ("(call-with-input-file " + json.dumps(str(path)) +
                          " (lambda (p) (let loop ((n 0)) (let ((x (read p))) "
                          "(if (eof-object? x) (displayln n) (loop (+ n 1)))))))")
            run(f"{label}-balance-{index}", [str(cache / "run.sh"), "gxi", "-e", expression])
            destination = output / f"{label}-syntax-{index}"
            destination.mkdir(exist_ok=args.resume)
            run(f"{label}-syntax-{index}", [str(cache / "run.sh"), "gxc", "-S", "-d", str(destination), str(path)])

    def apply(filename, cwd):
        patch = repository / "patches/gerbil-v19-darwin" / filename
        reverse = ["git", "apply", "--reverse", "--check", str(patch)]
        present = subprocess.run(reverse, cwd=cwd, capture_output=True).returncode == 0
        run(f"apply-{filename[:4]}", reverse if present else ["git", "apply", str(patch)], cwd)
        identity = {"file": patch.name, "sha256": hashlib.sha256(patch.read_bytes()).hexdigest()}
        if identity not in report["patches"]:
            report["patches"].append(identity)
        save()

    try:
        save()
        if not args.prepared_source:
            run("clone-gerbil", ["git", "clone", "--no-hardlinks", str(cache), str(source)])
            run("pin-gerbil", ["git", "checkout", "--detach", args.gerbil_ref], source)
            run("submodule-url", ["git", "config", "submodule.src/gambit.url", str(cache / "src/gambit")], source)
            run("clone-gambit", ["git", "-c", "protocol.file.allow=always", "submodule", "update", "--init"], source)
        elif subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=source, text=True).strip() != args.gerbil_ref:
            raise RuntimeError("prepared Gerbil source identity does not match")
        actual = subprocess.check_output(["git", "-C", str(source / "src/gambit"), "rev-parse", "HEAD"], text=True).strip()
        if actual != args.gambit_ref:
            raise RuntimeError("Gambit gitlink does not match the requested source")
        macros = subprocess.check_output([env["CC"], "-dM", "-E", "-x", "c", os.devnull], env=env, text=True)
        if "#define __clang__" in macros or "#define __GNUC__ 16\n" not in macros:
            raise RuntimeError("The selected compiler is not real GNU GCC 16")
        run("gcc-version", [env["CC"], "--version"])
        env["GERBIL_SOURCE"] = str(source / "src")
        env["GERBIL_VERSION_STRING"] = subprocess.check_output(["git", "describe", "--tags", "--always"], cwd=source, text=True).strip()
        run("version-context", [str(cache / "src/gambit/gsi/gsi"), f"-:~~={cache / 'build'}",
                                str(source / "src/build/build-version.scm")])
        if not args.prepared_source:
            check_sources("original")
        apply("0002-gerbil-streaming-compile-executor.patch", source)
        if not args.prepared_source:
            check_sources("0002")
        apply("0003-gerbil-darwin-executable-closure-dag.patch", source)
        if not args.prepared_source:
            check_sources("0003")
        else:
            prim_hash = hashlib.sha256((source / "src/gambit/gsc/_prims.scm").read_bytes()).hexdigest()
            if report.get("primitiveSourceSha256", prim_hash) != prim_hash:
                raise RuntimeError("prepared compiler source changed since its syntax qualification")
            context = '(##namespace ("c#"))(##include "src/gambit/lib/header.scm")(##include "src/gambit/gsc/_prims.scm")'
            run("primitive-context-syntax", ["./run.sh", "gxi", "-e",
                f'(##compile-top ##interaction-cte (##read-all-as-a-begin-expr-from-string {json.dumps(context)}))',
                "-e", '(displayln "PRIMITIVES-CONTEXT-SYNTAX-OK")'], source)
            report["primitiveSourceSha256"] = prim_hash
            report["preparedSource"] = True
            run("prepared-manifest", ["./manifest.sh"], source)
            report["preparedManifestSha256"] = hashlib.sha256((source / "MANIFEST").read_bytes()).hexdigest()
            protected = ("gsc/_prims.scm", "configure", "configure.ac", "lib/os_io.c")
            protected_hashes = {name: hashlib.sha256((source / "src/gambit" / name).read_bytes()).hexdigest()
                                for name in protected}
        run("configure", ["./configure", f"--prefix={output / 'install'}", f"--with-gambit={args.gambit_ref}",
                          "--enable-march=", "--enable-smp", "--enable-c-opt=-O1", "--enable-c-opt-rts=yes",
                          "--enable-gcc-opts", "--enable-inline-jumps", "--enable-dynamic-clib",
                          "--enable-trust-c-tco", "--enable-single-host=0"], source)
        if args.prepared_source:
            if any(hashlib.sha256((source / "src/gambit" / name).read_bytes()).hexdigest() != digest
                   for name, digest in protected_hashes.items()):
                raise RuntimeError("configure changed protected Gambit source; stop before compilation")
            report["preparedSourceSurvivedConfigure"] = True
        apply("0001-gambit-darwin-posix-spawn.patch", source / "src/gambit")
        if args.prepared_source:
            # 0012 supersedes 0004's placement; do not reapply the older patch.
            apply("0012-gambit-darwin-bootstrap-macro-tracking.patch", source / "src/gambit")
        else:
            apply("0004-gambit-darwin-gcc-macro-expansion.patch", source / "src/gambit")
            os.utime(source / "src/gambit/configure", None)
            run("recheck", ["./config.status", "--recheck"], source / "src/gambit")
            run("templates", ["./config.status"], source / "src/gambit")
            apply("0012-gambit-darwin-bootstrap-macro-tracking.patch", source / "src/gambit")
            os.utime(source / "src/gambit/configure", None)
            configuration = shlex.split(subprocess.check_output(
                ["./config.status", "--config"], cwd=source / "src/gambit", text=True))
            configuration = [f"CFLAGS={env['CFLAGS']} -foptimize-sibling-calls" if item.startswith("CFLAGS=")
                             else f"CC={env['CC']}" if item.startswith("CC=") else item for item in configuration
                             if item not in ("--no-create", "--no-recursion")]
            run("bootstrap-fix-configure", ["./configure", *configuration], source / "src/gambit")
        run("configure-shell-syntax", ["sh", "-n", "configure"], source / "src/gambit")
        makefile = (source / "src/gambit/makefile").read_text()
        compiler_line = next(line for line in makefile.splitlines() if line.startswith("C_COMPILER ="))
        cflags_line = next(line for line in makefile.splitlines() if line.startswith("FLAGS_OBJ ="))
        if "-ftrack-macro-expansion=0" not in compiler_line or "-ftrack-macro-expansion=0" in cflags_line:
            raise RuntimeError("Bootstrap macro policy is not exclusively on the inherited compiler command")
        report["bootstrapMacroTrackingSourceFix"] = True
        report["compilerCommand"] = compiler_line.split("=", 1)[1].strip()
        report.setdefault("hostLoadAtBuild", os.getloadavg())
        save()
        if args.continue_gambit_wip:
            gambit = source / "src/gambit"
            if hashlib.sha256((gambit / "boot/gsc/_prims.scm").read_bytes()).hexdigest() != report["primitiveSourceSha256"]:
                raise RuntimeError("saved WIP compiler does not contain the checked source")
            run("gambit-wip-complete", ["make", f"-j{cores}", "all"], gambit / "boot/gsc")
            run("gambit-wip-copy", ["make", "wip-gsc-boot"], gambit)
            run("gambit-head-bootstrap", ["make", f"-j{cores}", "bootstrap"], gambit)
            run("gambit-head-clean", ["make", "bootclean"], gambit)
            run("gambit-head-core", ["make", f"-j{cores}", "core"], gambit)
            build = source / "build"
            shutil.copy2(gambit / "gsi/gsi", source / "bootstrap/bin/gsi")
            for name in ("gsc/gsc", "bin/gambuild-C"):
                shutil.copy2(gambit / name, build / "bin" / Path(name).name)
            for pattern, destination in (("include/gambit.h", "include"), ("include/gambit-not*.h", "include"),
                                         ("lib/*#.scm", "lib"), ("gsc/*#.scm", "lib"),
                                         ("lib/_define-syntax.scm", "lib"), ("lib/_gambit.c", "lib")):
                for path in gambit.glob(pattern):
                    shutil.copy2(path, build / destination / path.name)
            for component, stem in (("lib", "libgambit"), ("gsi", "libgambitgsi"), ("gsc", "libgambitgsc")):
                for suffix in ("a", "so", "dylib"):
                    path = gambit / component / f"{stem}.{suffix}"
                    if path.exists():
                        shutil.copy2(path, build / "lib" / path.name)
            report["gambitWipContinuation"] = True
            save()
            stages = ("boot-gxi", "stage0", "stage1", "stdlib", "libgerbil", "lang", "tools")
        else:
            stages = ("prepare", "gambit", "boot-gxi", "stage0", "stage1", "stdlib", "libgerbil", "lang", "tools")
        for stage in stages:
            run(stage, ["./build.sh", stage], source)
        bootstrap_makefile = (source / "src/gambit/boot/makefile").read_text()
        if "-ftrack-macro-expansion=0" not in next(line for line in bootstrap_makefile.splitlines()
                                                  if line.startswith("C_COMPILER =")):
            raise RuntimeError("The actual archive bootstrap compiler lost macro tracking policy")
        run("version", ["./run.sh", "gxi", "-e", "(displayln (gerbil-version-string))"], source)
        run("base-tests", ["./run.sh", "gxi", ":gerbil/tools/gxtest", "-v", "5", "src/std/list/list-test.ss",
                           "src/std/vector/vector-test.ss", "src/std/values-test.ss", "src/std/iter/iter-test.ss"], source)
        tests = (output / "base-tests.log").read_text()
        if "HARNESS-OK" not in tests or tests.count("MODULE-OK") != 4 or not tests.rstrip().endswith("OK"):
            raise RuntimeError("The upstream base test harness did not qualify all four modules")
        report["baseTestCases"] = tests.count("CASE-OK")
        if report["baseTestCases"] != 45:
            raise RuntimeError("The upstream base tests did not exercise all 45 cases")
        contract = repository / "patches/gerbil-v19-darwin/tests/compiler-executor-contract.ss"
        run("executor-contract", ["./run.sh", "gxi", str(contract)], source)
        if "compiler executor contract passed" not in (output / "executor-contract.log").read_text():
            raise RuntimeError("The streaming executor contract did not report success")
        report["executorContractPassed"] = True
        report["qualified"] = True
        save()
    except BaseException as error:
        report["failure"] = str(error)
        save()
        raise


if __name__ == "__main__":
    main()
