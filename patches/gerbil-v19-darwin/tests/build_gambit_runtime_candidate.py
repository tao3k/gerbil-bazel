#!/usr/bin/env python3
"""Relink an isolated native Gerbil with selected Gambit C runtime edits."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
import os
from pathlib import Path
import platform
import shlex
import subprocess
import time

from bazel_host_environment import build_environment


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--objects", nargs="+", required=True)
    parser.add_argument("--syntax-only", action="store_true")
    parser.add_argument("--kernel-per-procedure-host", action="store_true")
    parser.add_argument("--kernel-keyword-outlining", action="store_true")
    parser.add_argument("--parameter-source-only", action="store_true")
    parser.add_argument("--native-pc-symbols", action="store_true")
    parser.add_argument("--reuse-std-generation-report", type=Path)
    parser.add_argument("--build-timeout-seconds", type=int, default=180)
    parser.add_argument("--scheme-runtime-optimization", choices=("O2", "O3", "O2-no-gcse"))
    parser.add_argument("--eval-source-cost-probe", action="store_true")
    args = parser.parse_args()
    if not 180 <= args.build_timeout_seconds <= 600:
        parser.error("build-only timeout must be between 180 and 600 seconds")
    if args.reuse_std_generation_report and not args.parameter_source_only:
        parser.error("STD generation reuse requires the parameter source experiment")
    repo = Path(__file__).resolve().parents[3]
    baseline, source, output = (p.resolve() for p in (args.baseline, args.source, args.output))
    if platform.system() != "Darwin" or not all(p.is_relative_to(repo / ".data") for p in (source, output)):
        parser.error("isolated Darwin sources and receipts under project .data required")
    allowed = {"os_dyn.o", "mem.o", "setup.o", "os_thread.o", "os_base.o", "os_files.o", "os_setup.o"}
    scheme_runtime = {"_eval.o", "_io.o", "_std.o", "_system.o", "_kernel.o", "_thread.o"}
    if args.eval_source_cost_probe:
        if (args.objects != ["_eval.o", "_gambit.o"] or args.scheme_runtime_optimization
                or args.native_pc_symbols or args.kernel_per_procedure_host
                or args.kernel_keyword_outlining or args.parameter_source_only):
            parser.error("EVAL boundary diagnostic requires original-O1 EVAL and static metadata")
        prepared = json.loads((source / "source-cost-preparation.json").read_text())
        lib = source / "src/gambit/lib"
        if (not prepared.get("fullMacroContextGenerationPassed")
                or prepared.get("cteIsolationChanged") or prepared.get("sourceLoadPolicyChanged")
                or prepared["sourceSha256"] != hashlib.sha256((lib / "_eval.scm").read_bytes()).hexdigest()
                or prepared["generatedCSha256"] != hashlib.sha256((lib / "_eval.c").read_bytes()).hexdigest()
                or prepared.get("generatedLinkCSha256") != hashlib.sha256((lib / "_gambit.c").read_bytes()).hexdigest()
                or prepared["headerSha256"] != hashlib.sha256((lib / "gambit-source-cost-probe.h").read_bytes()).hexdigest()):
            parser.error("EVAL diagnostic source provenance changed")
        allowed = {"_eval.o", "_gambit.o"}
    if args.native_pc_symbols:
        if (args.scheme_runtime_optimization or args.kernel_per_procedure_host
                or args.kernel_keyword_outlining or args.parameter_source_only or args.syntax_only):
            parser.error("native PC diagnostics require original Scheme runtime C and flags")
        allowed = scheme_runtime
    if args.scheme_runtime_optimization:
        allowed = scheme_runtime
    if args.kernel_per_procedure_host:
        if args.scheme_runtime_optimization or args.objects != ["_kernel.o"]:
            parser.error("kernel host isolation requires original optimization and only _kernel.o")
        allowed = {"_kernel.o"}
    if args.kernel_keyword_outlining:
        if args.scheme_runtime_optimization or args.kernel_per_procedure_host or args.objects != ["_kernel.o"]:
            parser.error("keyword outlining requires original optimization, original hosts and only _kernel.o")
        allowed = {"_kernel.o"}
    if args.parameter_source_only:
        if (args.scheme_runtime_optimization or args.kernel_per_procedure_host
                or args.kernel_keyword_outlining or args.objects != ["_std.o"]):
            parser.error("parameter source isolation requires original flags and only _std.o")
        allowed = {"_std.o"}
    if not set(args.objects) <= allowed:
        parser.error("only explicit Gambit C runtime objects are supported")
    output.mkdir(parents=True, exist_ok=False)
    env = build_environment()
    macros = subprocess.check_output([env["CC"], "-dM", "-E", "-x", "c", os.devnull], env=env, text=True)
    if "#define __clang__" in macros or "#define __GNUC__ 16\n" not in macros:
        raise RuntimeError("real GNU GCC 16 required")
    cores = int(subprocess.check_output(["sysctl", "-n", "hw.physicalcpu"], text=True))
    home, chome = baseline / "build", source / "build"
    env.update(GERBIL_HOME=str(home), GERBIL_PATH=str(output / "empty-user"),
               GERBIL_LOADPATH=str(home / "lib"), GERBIL_BUILD_CORES=str(cores),
               GAMBOPT=f"~~bin={home / 'bin'},~~lib={home / 'lib'},~~include={home / 'include'}",
               PATH=f"{home / 'bin'}:{env['PATH']}")
    env.pop("GERBIL_BUILD_PREFIX", None)
    env.pop("GAMBIT_HOST_GROUP_BUDGET", None)
    report = {"qualified": False, "performanceQualified": False, "cores": cores,
              "scope": "gambit-C-runtime-only", "objects": args.objects,
              "schemeRuntimeOptimization": args.scheme_runtime_optimization,
              "kernelPerProcedureHost": args.kernel_per_procedure_host,
              "kernelKeywordOutlining": args.kernel_keyword_outlining,
              "parameterSourceOnly": args.parameter_source_only,
              "buildTimeoutSeconds": args.build_timeout_seconds,
              "consumerFlagsChanged": False, "hostLoadStart": os.getloadavg()}
    if args.native_pc_symbols or args.eval_source_cost_probe:
        report["diagnosticOnly"] = True
    if args.eval_source_cost_probe:
        report["evalSourceCostProbe"] = True
        report["sourceCostPreparationSha256"] = hashlib.sha256(
            (source / "source-cost-preparation.json").read_bytes()).hexdigest()

    def invoke(name, argv, cwd=None, process_env=None):
        started = time.monotonic()
        with (output / f"{name}.log").open("w") as log:
            child = subprocess.Popen(argv, cwd=cwd, env=process_env or env,
                                     stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            try:
                while child.poll() is None:
                    try:
                        child.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        try:
                            parents = [line.split() for line in subprocess.check_output(
                                ["/bin/ps", "-axo", "pid,ppid"], text=True, timeout=3).splitlines()[1:]]
                            descendants = {child.pid}
                            for _ in range(5):
                                descendants.update(int(row[0]) for row in parents
                                                   if len(row) == 2 and int(row[1]) in descendants)
                            rows = [line.split(None, 2) for line in subprocess.check_output(
                                ["/bin/ps", "-p", ",".join(map(str, sorted(descendants))),
                                 "-o", "pid,time,comm"], text=True, timeout=3).splitlines()[1:]]
                            frontends = [(row[0], row[1]) for row in rows if len(row) == 3
                                         and Path(row[2]).name in ("cc1", "gsc", "gxi", "gerbil")]
                        except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
                            frontends = "observer-unavailable"
                        print(f"PROGRESS {name}: elapsed={time.monotonic() - started:.1f}s compiler-cpu={frontends}", flush=True)
                    if time.monotonic() - started > args.build_timeout_seconds:
                        raise TimeoutError(f"{name}: exceeded {args.build_timeout_seconds}-second build bound")
                status = child.returncode
            except BaseException:
                import signal
                os.killpg(child.pid, signal.SIGTERM)
                try:
                    child.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(child.pid, signal.SIGKILL)
                    child.wait()
                raise
        if status:
            raise RuntimeError(f"{name} failed; inspect retained log")
        print(f"OK {name}: {time.monotonic() - started:.3f}s", flush=True)

    try:
        lib = source / "src/gambit/lib"
        if args.native_pc_symbols:
            from gambit_pc_symbols import inject
            landmarks = []
            generated_files = []
            for obj in args.objects:
                path = lib / Path(obj).with_suffix(".c")
                original = path.read_text()
                if original != (baseline / "src/gambit/lib" / path.name).read_text():
                    raise RuntimeError("native PC diagnostic input differs from original runtime C")
                modified, rows = inject(original, len(landmarks))
                path.write_text(modified)
                landmarks.extend(rows)
                generated_files.append(str(path))
            report["nativePcLandmarks"] = len(landmarks)
            report["nativePcGeneratedFiles"] = generated_files
            report["nativePcGeneratorSha256"] = hashlib.sha256(
                Path(__file__).with_name("gambit_pc_symbols.py").read_bytes()).hexdigest()
            (output / "pc-landmarks.json").write_text(json.dumps(landmarks, indent=2) + "\n")
        if args.parameter_source_only:
            parameter = lib / "gambit/parameter/parameter.scm"
            report["parameterSourceSha256"] = hashlib.sha256(parameter.read_bytes()).hexdigest()
            context = f'(##include {json.dumps(str(lib / "header.scm"))})\n(##include {json.dumps(str(parameter))})'
            expression = ('(##compile-top ##interaction-cte '
                          f'(##read-all-as-a-begin-expr-from-string {json.dumps(context)}))')
            invoke("parameter-context-syntax", ["./run.sh", "gxi", "-e", expression,
                   "-e", '(displayln "PARAMETER-CONTEXT-SYNTAX-OK")'], cwd=source)
            if not (output / "parameter-context-syntax.log").read_text().rstrip().endswith("PARAMETER-CONTEXT-SYNTAX-OK"):
                raise RuntimeError("full parameter macro-context expansion did not pass")
            dry = subprocess.check_output(["make", "-n", "-B", "_std.c"], cwd=lib, env=env, text=True)
            commands = [shlex.split(line) for line in dry.splitlines() if line.startswith("../gsc-boot ")]
            if len(commands) != 1:
                raise RuntimeError("ambiguous official STD generation command")
            command = commands[0]
            command[0] = str(home / "bin/gsc")
            command[1] = f"-:~~bin={home / 'bin'},~~lib={lib},~~include={home / 'include'}"
            report["stdGenerationCommand"] = command
            report["generationGscSha256"] = hashlib.sha256((home / "bin/gsc").read_bytes()).hexdigest()
            if args.reuse_std_generation_report:
                evidence = args.reuse_std_generation_report.resolve()
                if not evidence.is_relative_to(repo / ".data"):
                    raise RuntimeError("generation evidence must stay under project .data")
                previous = json.loads(evidence.read_text())
                syntax_log = evidence.parent / "syntax-_std.o.log"
                if (not previous.get("parameterSourceOnly") or previous.get("consumerFlagsChanged")
                        or previous.get("parameterSourceSha256") != report["parameterSourceSha256"]
                        or previous.get("stdGenerationCommand") != command
                        or previous.get("sourceHashes", {}).get("_std.o") != hashlib.sha256((lib / "_std.c").read_bytes()).hexdigest()
                        or not syntax_log.exists() or "error:" in syntax_log.read_text(errors="replace")):
                    raise RuntimeError("STD generation evidence does not match this source and generated C")
                if previous.get("generationGscSha256") != report["generationGscSha256"]:
                    raise RuntimeError("original standalone GSC identity changed")
                report["reusedStdGenerationReportSha256"] = hashlib.sha256(evidence.read_bytes()).hexdigest()
                print("REUSE hash-qualified STD generation; native compilation still required", flush=True)
            else:
                invoke("generate-std", command, cwd=lib)
        commands_by_object = {}
        for obj in args.objects:
            make = ["make", "-n", "-B", obj]
            if args.scheme_runtime_optimization:
                options = "-O2 -fno-gcse" if args.scheme_runtime_optimization == "O2-no-gcse" else f"-{args.scheme_runtime_optimization}"
                make.append(f"FLAGS_OPT={options}")
            dry = subprocess.check_output(make, cwd=lib, env=env, text=True)
            commands = [shlex.split(line) for line in dry.splitlines()
                        if line.startswith(env["CC"] + " ")]
            if len(commands) != 1:
                raise RuntimeError(f"ambiguous official build command for {obj}")
            commands_by_object[obj] = commands[0]
            if args.kernel_per_procedure_host:
                commands_by_object[obj] += ["-U___SINGLE_HOST", "-g", "-fno-var-tracking",
                                            "-fno-var-tracking-assignments"]
            invoke(f"syntax-{obj}", [*commands[0], "-fsyntax-only"], cwd=lib)
        if args.syntax_only:
            report["qualified"] = True
            return
        report["sourceHashes"] = {obj: hashlib.sha256((lib / Path(obj).with_suffix(".c")).read_bytes()).hexdigest()
                                 for obj in args.objects}
        with ThreadPoolExecutor(max_workers=cores) as pool:
            pending = [pool.submit(invoke, f"compile-{obj}", command, lib)
                       for obj, command in commands_by_object.items()]
            for future in as_completed(pending):
                future.result()
        archive = chome / "lib/libgambit.a"
        invoke("replace-runtime-archive", ["/usr/bin/ar", "r", str(archive),
                                           *map(str, (lib / obj for obj in args.objects))])
        invoke("index-runtime-archive", ["/usr/bin/ranlib", str(archive)])
        expression = ('(import :std/encoding/json) '
                      f'(call-with-input-file {json.dumps(str(baseline / "src/build/build-bach.ss"))} '
                      '(lambda (p) (let lp () (let (f (read p)) '
                      '(cond ((eof-object? f) (error "builtin module list missing")) '
                      '((and (pair? f) (eq? (car f) \'def) (eq? (cadr f) \'builtin-modules)) '
                      '(displayln (json->string (list->vector (cadr (caddr f)))))) (else (lp)))))))')
        invoke("module-order", [str(home / "bin/gxi"), "-e", expression])
        modules = json.loads((output / "module-order.log").read_text().splitlines()[-1])
        static = home / "lib/static"
        cfiles = [static / (mod.replace("/", "__") + ".c") for mod in [*modules, "gerbil/main"]]
        link = output / "gerbil-link.c"
        invoke("generate-link", [str(home / "bin/gsc"), "-link", "-track-scheme",
                                 "-o", str(link), *map(str, cfiles)])
        e = dict(env)
        e.update(GAMBITDIR_INCLUDE=str(home / "include"), GAMBITDIR_LIB=str(home / "lib"),
                 BUILD_OBJ_INPUT_FILENAMES_PARAM=str(link), BUILD_OBJ_OUTPUT_FILENAME_PARAM=str(link.with_suffix(".o")),
                 BUILD_OBJ_META_INFO_FILE_PARAM=str(link))
        invoke("compile-link", [str(home / "bin/gambuild-C"), "obj"], process_env=e)
        invoke("link-native", [env["CC"], "-o", str(chome / "bin/gerbil"),
                               *map(str, (path.with_suffix(".o") for path in cfiles)), str(link.with_suffix(".o")),
                               str(archive), "-ldl", "-lm"])
        invoke("import-smoke", [str(chome / "bin/gxi"), "-e",
                               '(import :std/make :std/test :std/build-script) (displayln "IMPORT-OK")'])
        if not (output / "import-smoke.log").read_text().rstrip().endswith("IMPORT-OK"):
            raise RuntimeError("native framework smoke failed")
        report["binaryHashes"] = {name: hashlib.sha256((chome / "bin" / name).read_bytes()).hexdigest()
                                  for name in ("gxi", "gsc")}
        report["gscUnchanged"] = report["binaryHashes"]["gsc"] == hashlib.sha256((home / "bin/gsc").read_bytes()).hexdigest()
        report["qualified"] = True
    except BaseException as error:
        report["failure"] = repr(error)
        raise
    finally:
        report["hostLoadEnd"] = os.getloadavg()
        (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
