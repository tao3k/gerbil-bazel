#!/usr/bin/env python3
"""Rebuild selected Darwin macro-expansion runtime objects, not consumer flags."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import signal
import subprocess
import time

from bazel_host_environment import build_environment
from gambit_host_coalescing import render as render_coalesced_hosts
from gambit_rest_registers import inject as inject_rest_registers


def resume_link(args):
    output, baseline = args.output.resolve(), args.baseline.resolve()
    repo = Path(__file__).resolve().parents[3]
    if platform.system() != "Darwin" or not output.is_relative_to(repo / ".data"):
        raise RuntimeError("isolated Darwin profile required")
    prior = json.loads((output / "report.json").read_text())
    if prior.get("qualified") or prior.get("failure") != "compile-link exceeded 300 seconds":
        raise RuntimeError("resume requires a retained compile-link timeout")
    if prior.get("retainedRuntimeLinkers") or prior.get("privateRegisterBridge"):
        raise RuntimeError("resume only supports the original eleven-module carrier")
    destination = output / "resume-link-report.json"
    if destination.exists():
        raise RuntimeError("resume receipt already exists; do not overwrite evidence")
    candidate = output / "source"
    home, chome = baseline / "build", candidate / "build"
    link = output / "gerbil-link.c"
    modules = json.loads((output / "module-order.log").read_text().splitlines()[-1])
    objects = [chome / "lib/static" / (mod.replace("/", "__") + ".o")
               for mod in [*modules, "gerbil/main"]]
    digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    for row in prior["objects"]:
        stem = chome / "lib/static" / row["module"].replace("/", "__")
        if digest(stem.with_suffix(".c")) != row["generatedCSha256"] or digest(stem.with_suffix(".o")) != row["objectSha256"]:
            raise RuntimeError("existing source/object hash drift")
    env = build_environment()
    macros = subprocess.check_output([env["CC"], "-dM", "-E", "-x", "c", os.devnull], env=env, text=True)
    if "#define __clang__" in macros or "#define __GNUC__ 16\n" not in macros:
        raise RuntimeError("real GNU GCC 16 required")
    env.pop("GERBIL_BUILD_PREFIX", None)
    env.pop("GAMBIT_HOST_GROUP_BUDGET", None)
    env.update(GERBIL_HOME=str(home), GERBIL_PATH=str(output / "resume-empty-user"),
               GERBIL_LOADPATH=str(home / "lib"),
               GERBIL_BUILD_CORES=str(prior["cores"]),
               GAMBOPT=f"~~bin={home / 'bin'},~~lib={home / 'lib'},~~include={home / 'include'}",
               PATH=f"{home / 'bin'}:{env['PATH']}")
    report = {"qualified": False, "performanceQualified": False,
              "scope": "unchanged-generated-c-link-resume-partial-runtime",
              "compileWallBudgetSeconds": 600, "cores": prior["cores"],
              "priorFailure": prior["failure"], "generatedLinkSha256": digest(link),
              "objectsSha256": [digest(path) for path in objects], "runs": []}
    def run(name, command, process_env):
        started = time.monotonic()
        with (output / f"resume-{name}.log").open("w") as log:
            child = subprocess.Popen(command, env=process_env, stdout=log,
                                     stderr=subprocess.STDOUT, start_new_session=True)
            try:
                while child.poll() is None:
                    try:
                        child.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        print(f"RESUME-ACTIVE {name}: {time.monotonic()-started:.1f}s", flush=True)
                    if child.poll() is None and time.monotonic() - started > 600:
                        raise TimeoutError("link resume exceeded 600-second build budget")
            finally:
                if child.poll() is None:
                    os.killpg(child.pid, signal.SIGTERM)
                    try:
                        child.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        os.killpg(child.pid, signal.SIGKILL)
                        child.wait()
        report["runs"].append({"name": name, "exitCode": child.returncode,
                               "wallSeconds": time.monotonic() - started})
        if child.returncode:
            raise RuntimeError(f"{name} failed: {child.returncode}")
        print(f"RESUME-OK {name}", flush=True)
    try:
        e = dict(env, GAMBITDIR_INCLUDE=str(chome / "include"), GAMBITDIR_LIB=str(chome / "lib"),
                 BUILD_OBJ_INPUT_FILENAMES_PARAM=str(link),
                 BUILD_OBJ_OUTPUT_FILENAME_PARAM=str(link.with_suffix(".o")),
                 BUILD_OBJ_META_INFO_FILE_PARAM=str(link))
        run("compile-link", [str(home / "bin/gambuild-C"), "obj"], e)
        if digest(link) != report["generatedLinkSha256"]:
            raise RuntimeError("generated C changed during resume")
        run("link-bach", [env["CC"], "-o", str(chome / "bin/gerbil"), *map(str, objects),
                          str(link.with_suffix(".o")), f"-L{chome / 'lib'}", "-lgambit", "-ldl", "-lm"], env)
        e = dict(env)
        e["PATH"] = f"{chome / 'bin'}:{env['PATH']}"
        run("import-smoke", [str(chome / "bin/gxi"), "-e",
                             '(import :std/make :std/test :std/build-script) (displayln "IMPORT-OK")'], e)
        if not (output / "resume-import-smoke.log").read_text().rstrip().endswith("IMPORT-OK"):
            raise RuntimeError("resumed native import failed")
        report["binaryHashes"] = {name: digest(chome / "bin" / name) for name in ("gxi", "gsc")}
        if report["binaryHashes"]["gsc"] != digest(home / "bin/gsc"):
            raise RuntimeError("resume changed GSC")
        report["qualified"] = True
    except BaseException as error:
        report["failure"] = str(error)
        raise
    finally:
        report["hostLoadEnd"] = os.getloadavg()
        destination.write_text(json.dumps(report, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--resume-link", action="store_true")
    parser.add_argument("--compile-wall-budget-seconds", type=int, default=300)
    parser.add_argument("--optimization", choices=("O1", "O3", "O2-no-gcse", "O1-default"), default="O3")
    parser.add_argument("--sampled-hot-path", action="store_true")
    parser.add_argument("--per-procedure-host", action="store_true")
    parser.add_argument("--host-count-probe", action="store_true")
    parser.add_argument("--distributed-host-exit", action="store_true")
    parser.add_argument("--private-register-bridge", action="store_true")
    parser.add_argument("--fixed-gvm-registers", action="store_true")
    parser.add_argument("--bridge-edge-probe", action="store_true")
    parser.add_argument("--structure-instance-inline", action="store_true")
    parser.add_argument("--structure-instance-count", action="store_true")
    parser.add_argument("--primitive-call-count", action="store_true")
    parser.add_argument("--host-exit-count", action="store_true")
    parser.add_argument("--bridge-hot-edges", action="store_true")
    parser.add_argument("--structure-instance-expansion", action="store_true")
    parser.add_argument("--primitive-expansion-hook", type=Path)
    parser.add_argument("--module-local-global-table", action="store_true")
    parser.add_argument("--external-call-layout", action="store_true")
    parser.add_argument("--coalesce-original-hosts", action="store_true")
    parser.add_argument("--coalesce-exclude", action="append", default=[])
    parser.add_argument("--coalesce-kernel", action="store_true")
    parser.add_argument("--guarded-global-jumps", action="store_true")
    parser.add_argument("--return-label-count", action="store_true")
    parser.add_argument("--gen-entry-count", action="store_true")
    parser.add_argument("--vector-entry-guards", action="store_true")
    parser.add_argument("--guarded-leaf-clones", action="store_true")
    parser.add_argument("--internal-leaf-clones", action="store_true")
    parser.add_argument("--known-return-guards", action="store_true")
    parser.add_argument("--local-subroutine-clones", action="store_true")
    parser.add_argument("--defer-local-frames", action="store_true")
    parser.add_argument("--guarded-readonly-traces", action="store_true")
    parser.add_argument("--guarded-trace-polls", action="store_true")
    parser.add_argument("--guarded-trace-restart-polls", action="store_true")
    parser.add_argument("--guarded-trace-coalesce-polls", action="store_true")
    parser.add_argument("--guarded-trace-primitive-boundary", action="store_true")
    parser.add_argument("--guarded-trace-epoch-cache", action="store_true")
    parser.add_argument("--guarded-trace-inline-lookup", action="store_true")
    parser.add_argument("--guarded-trace-outline-lookup", action="store_true")
    parser.add_argument("--guarded-trace-lookup-return-branches", action="store_true")
    parser.add_argument("--supplementary-pure-branches", action="store_true")
    parser.add_argument("--supplementary-fresh-branches", action="store_true")
    parser.add_argument("--scalar-caller-label", action="append", default=[])
    parser.add_argument("--scalar-boundary-label", action="append", default=[])
    parser.add_argument("--small-hash-scan", action="store_true")
    parser.add_argument("--small-hash-scan-count", action="store_true")
    parser.add_argument("--parameter-entry-fastpath", action="store_true")
    parser.add_argument("--parameter-identity-return", action="store_true")
    parser.add_argument("--parameter-env-lookup", action="store_true")
    parser.add_argument("--bounded-primitive-entries", action="store_true")
    parser.add_argument("--guarded-trace-count", action="store_true")
    parser.add_argument("--guarded-trace-allocations", action="store_true")
    parser.add_argument("--native-pc-symbols", action="store_true")
    parser.add_argument("--local-return-guards", action="store_true")
    parser.add_argument("--cache-label-bases", action="store_true")
    parser.add_argument("--kernel-label-count", action="store_true")
    parser.add_argument("--runtime-label-unit", choices=("kernel", "std"), default="kernel")
    parser.add_argument("--rest-register-fastpath", action="store_true")
    parser.add_argument("--native-structure-jump", action="store_true")
    parser.add_argument("--native-structure-jump-count", action="store_true")
    parser.add_argument("--native-structure-expression", action="store_true")
    args = parser.parse_args()
    if not 300 <= args.compile_wall_budget_seconds <= 1200:
        parser.error("compile wall budget must be between 300 and 1200 seconds")
    if args.native_pc_symbols and args.optimization != "O1":
        parser.error("native PC symbols require original O1")
    if args.parameter_entry_fastpath and (not args.coalesce_original_hosts or
            (args.guarded_trace_epoch_cache and not args.parameter_identity_return)):
        parser.error("parameter entry requires original hosts and explicit identity/coherence mode for epochs")
    if args.parameter_identity_return and not args.parameter_entry_fastpath:
        parser.error("identity return requires guarded parameter entry")
    if args.parameter_env_lookup and not args.parameter_identity_return:
        parser.error("environment lookup requires identity/coherence mode")
    if args.bounded_primitive_entries and not args.coalesce_original_hosts:
        parser.error("bounded primitive entries require original host coalescing")
    if args.guarded_trace_lookup_return_branches and not args.guarded_trace_inline_lookup:
        parser.error('lookup return branches require precise lookup fallback')
    if args.runtime_label_unit != "kernel" and not args.kernel_label_count:
        parser.error("runtime label selection requires the diagnostic counter")
    if args.guarded_trace_polls and not args.guarded_readonly_traces:
        parser.error("trace polls require readonly traces")
    if args.guarded_trace_allocations and (not args.guarded_trace_restart_polls
            or args.guarded_trace_coalesce_polls or args.guarded_trace_primitive_boundary
            or args.guarded_trace_epoch_cache or args.guarded_trace_inline_lookup):
        parser.error("allocation traces require individual restart polls and no external effects")
    if args.guarded_trace_restart_polls and not args.guarded_trace_polls:
        parser.error("restart polls require trace polls")
    if args.guarded_trace_coalesce_polls and not args.guarded_trace_restart_polls:
        parser.error("coalesced polls require readonly restart")
    if args.guarded_trace_primitive_boundary and not args.guarded_readonly_traces:
        parser.error("primitive boundary requires readonly traces")
    if args.guarded_trace_epoch_cache and not args.guarded_trace_coalesce_polls:
        parser.error("epoch cache requires coalesced polls")
    if args.guarded_trace_inline_lookup and (args.guarded_trace_epoch_cache or not args.guarded_trace_coalesce_polls or not args.guarded_trace_primitive_boundary):
        parser.error("inline lookup requires uncached coalesced primitive traces")
    if args.guarded_trace_outline_lookup and not args.guarded_trace_inline_lookup:
        parser.error("outlined lookup requires inline lookup")
    if args.guarded_trace_count and not args.guarded_readonly_traces:
        parser.error("trace counters require readonly traces")
    if args.small_hash_scan and not args.coalesce_original_hosts:
        parser.error("small hash scan requires an isolated coalesced carrier")
    if args.small_hash_scan_count and not args.small_hash_scan:
        parser.error("small hash scan counters require the scan experiment")
    if args.supplementary_fresh_branches and args.supplementary_pure_branches:
        parser.error("supplementary fresh and pure trees are separate experiments")
    if args.scalar_caller_label and (not args.guarded_readonly_traces or not args.guarded_trace_lookup_return_branches
            or args.supplementary_fresh_branches or args.supplementary_pure_branches
            or args.guarded_trace_allocations or args.guarded_trace_epoch_cache):
        parser.error("caller scalarization requires the best uncached readonly return-branch carrier only")
    if args.scalar_boundary_label and (not args.guarded_readonly_traces or not args.guarded_trace_lookup_return_branches
            or args.scalar_caller_label or args.supplementary_fresh_branches or args.supplementary_pure_branches
            or args.guarded_trace_allocations or args.guarded_trace_epoch_cache or args.small_hash_scan):
        parser.error("boundary scalarization requires the unchanged best uncached carrier only")
    if (args.supplementary_pure_branches or args.supplementary_fresh_branches) and (not args.guarded_readonly_traces
            or args.guarded_trace_allocations or args.guarded_trace_epoch_cache):
        parser.error("supplementary pure trees require readonly nontransactional uncached traces")
    if args.resume_link:
        resume_link(args)
        return
    if args.guarded_readonly_traces and (not args.coalesce_original_hosts or any((
            args.guarded_global_jumps, args.return_label_count, args.gen_entry_count,
            args.vector_entry_guards, args.guarded_leaf_clones, args.internal_leaf_clones,
            args.known_return_guards, args.local_subroutine_clones, args.local_return_guards,
            args.cache_label_bases, args.coalesce_kernel))):
        parser.error("readonly traces require an isolated original-host carrier")
    if args.defer_local_frames and not args.local_subroutine_clones:
        parser.error("deferred frames require the checked local-subroutine carrier")
    if args.local_subroutine_clones and (not args.coalesce_original_hosts or args.known_return_guards or args.guarded_leaf_clones or args.gen_entry_count or args.return_label_count):
        parser.error("local subroutine copies require an isolated original-host profile")
    if args.coalesce_exclude and not args.coalesce_original_hosts:
        parser.error("coalescing exclusions require the original host carrier")
    if args.cache_label_bases and not args.coalesce_original_hosts:
        parser.error("label base snapshots require the original host carrier")
    if args.native_structure_jump_count and not args.native_structure_jump:
        parser.error("native structure counters require the native jump prototype")
    if args.native_structure_expression and (args.native_structure_jump or not args.structure_instance_expansion or not args.primitive_expansion_hook):
        parser.error("native expression requires its own checked expansion hook")
    if args.guarded_global_jumps and not args.coalesce_original_hosts:
        parser.error("guarded global jumps require host coalescing")
    if args.return_label_count and not args.coalesce_original_hosts:
        parser.error("return label counts require host coalescing")
    if args.gen_entry_count and (not args.coalesce_original_hosts or args.return_label_count or args.local_return_guards):
        parser.error("generic entry counts require a separate coalesced diagnostic")
    if args.vector_entry_guards and (not args.coalesce_original_hosts or args.gen_entry_count or args.return_label_count):
        parser.error("vector entry guards require a noninstrumented coalesced profile")
    if args.guarded_leaf_clones and (not args.guarded_global_jumps or args.vector_entry_guards or args.gen_entry_count or args.return_label_count):
        parser.error("leaf clones require a separate guarded global coalescing profile")
    if args.internal_leaf_clones and not args.guarded_leaf_clones:
        parser.error("internal copies require the checked leaf clone carrier")
    if args.known_return_guards and (not args.coalesce_original_hosts or args.guarded_leaf_clones or args.vector_entry_guards or args.gen_entry_count or args.return_label_count):
        parser.error("known return guards require a separate original-host profile")
    if args.local_return_guards and (not args.coalesce_original_hosts or args.return_label_count):
        parser.error("local return guards require a separate coalesced profile")
    if args.native_structure_jump and (not args.structure_instance_expansion or not args.primitive_expansion_hook):
        parser.error("native structure jump requires its checked compiler hook")
    if args.rest_register_fastpath and (args.optimization != "O1" or
            any((args.coalesce_original_hosts, args.kernel_label_count, args.module_local_global_table,
                 args.external_call_layout, args.primitive_expansion_hook, args.structure_instance_expansion,
                 args.structure_instance_inline, args.structure_instance_count, args.primitive_call_count,
                 args.host_exit_count, args.private_register_bridge, args.host_count_probe,
                 args.distributed_host_exit, args.per_procedure_host))):
        parser.error("rest register fast path requires an isolated original O1 profile")
    if args.kernel_label_count and (args.optimization != "O1" or args.coalesce_original_hosts or
            any((args.module_local_global_table, args.external_call_layout, args.primitive_expansion_hook,
                 args.structure_instance_expansion, args.structure_instance_inline, args.structure_instance_count,
                 args.primitive_call_count, args.host_exit_count, args.private_register_bridge,
                 args.host_count_probe, args.distributed_host_exit, args.per_procedure_host))):
        parser.error("kernel label count requires an isolated original runtime profile")
    if args.coalesce_kernel and not args.coalesce_original_hosts:
        parser.error("kernel requires original host coalescing")
    if (args.module_local_global_table or args.external_call_layout or args.coalesce_original_hosts) and (args.optimization != "O1" or
            any((args.structure_instance_expansion, args.structure_instance_inline,
                 args.structure_instance_count, args.primitive_call_count,
                 args.host_exit_count, args.private_register_bridge,
                 args.host_count_probe, args.distributed_host_exit,
                 args.per_procedure_host, args.bridge_edge_probe, args.bridge_hot_edges))):
        parser.error("module-local table probe requires original O1 and no other prototype")
    if sum((args.module_local_global_table, args.external_call_layout, args.coalesce_original_hosts)) > 1:
        parser.error("binding, call-layout and host-coalescing probes must be measured separately")
    if args.primitive_expansion_hook and not args.structure_instance_expansion:
        parser.error("a custom primitive hook requires primitive expansion mode")
    if args.bridge_edge_probe and not args.private_register_bridge:
        parser.error("edge probe requires private bridge")
    if args.fixed_gvm_registers and (not args.private_register_bridge
            or args.bridge_edge_probe or args.bridge_hot_edges):
        parser.error("fixed GVM registers require an uninstrumented private bridge")
    if args.bridge_hot_edges and (not args.private_register_bridge or not args.sampled_hot_path or args.bridge_edge_probe):
        parser.error("hot edges require all eleven private bridge units and no edge instrumentation")
    structure_probe = args.structure_instance_inline or args.structure_instance_count or args.primitive_call_count or args.host_exit_count
    if args.structure_instance_expansion and (structure_probe or args.optimization != "O1"
            or args.private_register_bridge or args.host_count_probe or args.distributed_host_exit or args.per_procedure_host):
        parser.error("primitive expansion requires original O1/host mode and no C runtime prototype")
    if structure_probe and (args.optimization != "O1" or args.private_register_bridge
                            or args.host_count_probe or args.distributed_host_exit
                            or args.per_procedure_host
                            or sum((args.structure_instance_inline, args.structure_instance_count,
                                    args.primitive_call_count, args.host_exit_count)) > 1):
        parser.error("structure primitive probe requires original O1/host mode and no other prototype")
    if args.per_procedure_host and (args.optimization != "O1" or args.sampled_hot_path):
        parser.error("host isolation requires original O1 and only the two sampled expander units")
    if args.host_count_probe and (args.optimization != "O1" or args.per_procedure_host):
        parser.error("entry count diagnostics require original O1 and original single-host mode")
    if args.distributed_host_exit and (args.optimization != "O1" or args.per_procedure_host
                                      or args.host_count_probe):
        parser.error("distributed exits require original O1, host mode and no counting probe")
    if args.private_register_bridge and (args.optimization != "O1" or args.per_procedure_host
                                        or args.host_count_probe or args.distributed_host_exit):
        parser.error("private bridge requires original O1, host mode and no other prototype")
    repo = Path(__file__).resolve().parents[3]
    output = args.output.resolve()
    if platform.system() != "Darwin" or not output.is_relative_to(repo / ".data"):
        parser.error("Darwin-only profile experiment under project .data required")
    output.mkdir(parents=True, exist_ok=False)
    baseline = args.baseline.resolve()
    env = build_environment()
    macros = subprocess.check_output([env["CC"], "-dM", "-E", "-x", "c", os.devnull], env=env, text=True)
    if "#define __clang__" in macros or "#define __GNUC__ 16\n" not in macros:
        raise RuntimeError("real GNU GCC 16 required")
    cores = int(subprocess.check_output(["sysctl", "-n", "hw.physicalcpu"], text=True))
    home = baseline / "build"
    env.pop("GERBIL_BUILD_PREFIX", None)
    env.pop("GAMBIT_HOST_GROUP_BUDGET", None)
    env.update(GERBIL_HOME=str(home), GERBIL_PATH=str(output / "empty-user"),
               GERBIL_LOADPATH=str(home / "lib"), GERBIL_BUILD_CORES=str(cores),
               GAMBOPT=f"~~bin={home / 'bin'},~~lib={home / 'lib'},~~include={home / 'include'}",
               PATH=f"{home / 'bin'}:{env['PATH']}")
    report = {"qualified": False, "performanceQualified": False,
              "scope": "macro-expansion-runtime-profile-only", "cores": cores,
              "runtimeOptimization": args.optimization,
              "compileWallBudgetSeconds": args.compile_wall_budget_seconds,
              "consumerFlagsChanged": False, "hostLoadStart": os.getloadavg(), "objects": []}

    def save():
        (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")

    def invoke(name, command, process_env=None):
        started = time.monotonic()
        budget = args.compile_wall_budget_seconds if name == "compile-link" else 300
        with (output / f"{name}.log").open("w") as log:
            child = subprocess.Popen(command, env=process_env or env, stdout=log,
                                     stderr=subprocess.STDOUT, start_new_session=True)
            try:
                while True:
                    try:
                        code = child.wait(timeout=10)
                        break
                    except subprocess.TimeoutExpired:
                        elapsed = time.monotonic() - started
                        print(f"ACTIVE {name}: {elapsed:.1f}s, pid {child.pid}", flush=True)
                        if elapsed > budget:
                            raise TimeoutError(f"{name} exceeded {budget} seconds")
            finally:
                if child.poll() is None:
                    os.killpg(child.pid, signal.SIGTERM)
                    try:
                        child.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        os.killpg(child.pid, signal.SIGKILL)
                        child.wait()
        if code:
            raise RuntimeError(f"{name} failed; inspect its retained log")
        return time.monotonic() - started

    try:
        save()
        script_path = baseline / "src/build/build-bach.ss"
        expression = ('(import :std/encoding/json) '
                      f'(call-with-input-file {json.dumps(str(script_path))} '
                      '(lambda (p) (let lp () (let (f (read p)) '
                      '(cond ((eof-object? f) (error "builtin module list missing")) '
                      '((and (pair? f) (eq? (car f) \'def) '
                      '(eq? (cadr f) \'builtin-modules)) '
                      '(displayln (json->string (list->vector (cadr (caddr f)))))) '
                      '(else (lp)))))))')
        invoke("module-order", [str(home / "bin/gxi"), "-e", expression])
        modules = json.loads((output / "module-order.log").read_text().splitlines()[-1])
        candidate = output / "source"
        invoke("clone-toolchain", ["/bin/cp", "-cR", str(baseline), str(candidate)])
        chome = candidate / "build"
        static = chome / "lib/static"
        # These units are on the previously sampled eager-import/expansion path.
        selected = ("gerbil/expander/core", "gerbil/expander/module",
                    "gerbil/expander/compile", "gerbil/expander/stx",
                    "gerbil/expander/stxcase", "gerbil/runtime/hash", "gerbil/runtime/table")
        if args.sampled_hot_path:
            selected += ("gerbil/expander/top", "gerbil/runtime/mop",
                         "gerbil/runtime/interface", "gerbil/runtime/util")
        if args.per_procedure_host:
            selected = ("gerbil/expander/core", "gerbil/expander/stx")
        if args.kernel_label_count:
            selected = ()
        options = {"O2-no-gcse": "-O2 -fno-gcse",
                   "O1-default": "-O1 -fexpensive-optimizations -fno-gcse"}.get(
                       args.optimization, f"-{args.optimization}")
        if args.native_structure_expression:
            expression_header = output / "gambit-structure-native-expression.h"
            expression_header.write_bytes(Path(__file__).with_name(expression_header.name).read_bytes())
            report["nativeStructureExpressionHeaderSha256"] = hashlib.sha256(expression_header.read_bytes()).hexdigest()
            report["nativeStructureExpression"] = True
            options += f" -include {expression_header}"
        if args.native_structure_jump_count:
            counter_header = output / "gambit-structure-jump-count.h"
            counter_header.write_bytes(Path(__file__).with_name(counter_header.name).read_bytes())
            report["nativeStructureJumpCounterSha256"] = hashlib.sha256(counter_header.read_bytes()).hexdigest()
            options += f" -include {counter_header}"
        if args.native_structure_jump:
            native_header = output / "gambit-structure-native-jump.h"
            native_header.write_bytes(Path(__file__).with_name(native_header.name).read_bytes())
            report["nativeStructureJumpHeaderSha256"] = hashlib.sha256(native_header.read_bytes()).hexdigest()
            report["nativeStructureJump"] = True
            options += f" -include {native_header}"
        rest_header = None
        if args.rest_register_fastpath:
            rest_header = output / "gambit-rest-register-fastpath.h"
            rest_header.write_bytes(Path(__file__).with_name(rest_header.name).read_bytes())
            report["restRegisterHeaderSha256"] = hashlib.sha256(rest_header.read_bytes()).hexdigest()
        if args.per_procedure_host:
            options += " -U___SINGLE_HOST"
        report["sampledHotPath"] = args.sampled_hot_path
        report["runtimeCcOptions"] = options
        report["perProcedureHost"] = args.per_procedure_host
        report["hostCountProbe"] = args.host_count_probe
        report["distributedHostExit"] = args.distributed_host_exit
        report["privateRegisterBridge"] = args.private_register_bridge
        report["fixedGvmRegisters"] = args.fixed_gvm_registers
        report["bridgeEdgeProbe"] = args.bridge_edge_probe
        report["bridgeHotEdges"] = args.bridge_hot_edges
        if args.bridge_hot_edges:
            options += " -DGB_BRIDGE_HOT_EDGES"
        if args.bridge_edge_probe:
            options += " -DGB_BRIDGE_EDGE_PROBE"
        if args.structure_instance_count:
            options += " -DGB_STRUCTURE_COUNT_ONLY"
        report["runtimeCcOptions"] = options
        report["structureInstanceInline"] = args.structure_instance_inline
        report["structureInstanceCount"] = args.structure_instance_count
        report["primitiveCallCount"] = args.primitive_call_count
        report["hostExitCount"] = args.host_exit_count
        structure_header = None
        if structure_probe:
            structure_header = output / ("gambit-host-exit-count.h" if args.host_exit_count else
                                         "gambit-primitive-call-count.h" if args.primitive_call_count
                                         else "gambit-structure-instance-probe.h")
            structure_header.write_bytes(Path(__file__).with_name(structure_header.name).read_bytes())
            report["structureProbeHeaderSha256"] = hashlib.sha256(structure_header.read_bytes()).hexdigest()
        bridge_header = None
        if args.private_register_bridge:
            bridge_header = output / ("gambit-fixed-gvm-bridge.h" if args.fixed_gvm_registers
                                      else "gambit-private-register-bridge.h")
            bridge_header.write_bytes(Path(__file__).with_name(bridge_header.name).read_bytes())
            report["privateBridgeHeaderSha256"] = hashlib.sha256(bridge_header.read_bytes()).hexdigest()
            if args.fixed_gvm_registers:
                state = output / "gambit-fixed-gvm-state.h"
                state.write_bytes(Path(__file__).with_name(state.name).read_bytes())
                report["fixedGvmStateSha256"] = hashlib.sha256(state.read_bytes()).hexdigest()
        builder = home / "bin/gambuild-C"
        expansion_hook = None
        expansion_prelude = []
        if args.structure_instance_expansion:
            expansion_hook = output / "gambit-structure-expander-hook.scm"
            original_hook = args.primitive_expansion_hook.resolve() if args.primitive_expansion_hook else Path(__file__).with_name(expansion_hook.name)
            if not original_hook.is_relative_to(repo):
                raise RuntimeError("primitive hook must be project-local")
            expansion_hook.write_bytes(original_hook.read_bytes())
            report["primitiveExpansionHookSha256"] = hashlib.sha256(expansion_hook.read_bytes()).hexdigest()
            invoke("runtime-smp", [str(home / "bin/gxi"), "-e",
                                   '(displayln (if (gerbil-runtime-smp?) "yes" "no"))'])
            smp = (output / "runtime-smp.log").read_text().strip() == "yes"
            report["runtimeSmp"] = smp
            expansion_prelude = (["-e", "(define-cond-expand-feature|enable-smp|)"] if smp else [])
            expansion_prelude += ["-e", f'(include {json.dumps(str(home / "lib/_gambit#.scm"))})',
                                  "-e", f'(load {json.dumps(str(expansion_hook))})']
        report["structureInstanceExpansion"] = args.structure_instance_expansion

        pc_sources = {}
        if args.native_pc_symbols and not args.coalesce_original_hosts:
            from gambit_pc_symbols import inject as inject_pc_symbols
            landmarks = []
            for mod in selected:
                cfile = static / (mod.replace("/", "__") + ".c")
                content, rows = inject_pc_symbols(cfile.read_text(), len(landmarks))
                pc_sources[mod] = content
                landmarks.extend(rows)
            (output / "pc-landmarks.json").write_text(json.dumps(landmarks, indent=2) + "\n")
            report["nativePcLandmarks"] = len(landmarks)
            report["nativePcModuleFiles"] = [mod.replace("/", "__") + ".c" for mod in selected]
            report["nativePcGeneratorSha256"] = hashlib.sha256(
                Path(__file__).with_name("gambit_pc_symbols.py").read_bytes()).hexdigest()

        def compile_object(mod):
            stem = mod.replace("/", "__")
            cfile, obj = static / f"{stem}.c", static / f"{stem}.o"
            original_hash = hashlib.sha256(cfile.read_bytes()).hexdigest()
            expansion_count = None
            rest_sites = 0
            if args.rest_register_fastpath:
                content, rest_sites = inject_rest_registers(cfile.read_text(), rest_header)
                cfile.write_text(content)
            if args.module_local_global_table:
                content = cfile.read_text()
                boundary = '#include "gambit.h"'
                if content.count(boundary) != 1:
                    raise RuntimeError("unique Gambit header boundary required")
                prefix = "#if defined(__APPLE__) && defined(__GNUC__) && !defined(__clang__)\n#define ___BIND_LATE\n#endif\n"
                cfile.write_text(content.replace(boundary, prefix + boundary))
            if args.external_call_layout:
                content = cfile.read_text()
                boundary = '#include "gambit.h"'
                if content.count(boundary) != 1:
                    raise RuntimeError("unique Gambit header boundary required")
                definitions = r'''
#if defined(__APPLE__) && defined(__GNUC__) && !defined(__clang__) && defined(___USE_LABEL_VALUES) && defined(___INLINE_JUMPS)
#define GB_JUMP_CALL(dest) {___pc=dest; if (___EXPECT_TRUE(___LABEL_HOST_GET(___pc) != ___HOST_PROC)) goto ___jumpext; goto *___LABEL_HOST_LABEL_GET(___pc);}
#undef ___JUMPGENNOTSAFE
#undef ___JUMPGLONOTSAFE
#undef ___JUMPGENSAFE
#undef ___JUMPGLOSAFE
#define ___JUMPGENNOTSAFE(nargs,val) {nargs ___SELF=val; GB_JUMP_CALL(___LABEL_ENTRY_GET(___SELF))}
#define ___JUMPGLONOTSAFE(nargs,i,glo) ___JUMPGENNOTSAFE(nargs,___GLO(i,glo))
#ifdef ___NOT_SAFE_CALLS
#define ___JUMPGENSAFE(nargs,val) ___JUMPGENNOTSAFE(nargs,val)
#define ___JUMPGLOSAFE(nargs,i,glo) ___JUMPGLONOTSAFE(nargs,i,glo)
#else
#define ___JUMPGENSAFE(nargs,val) {nargs ___SELF=val; if (___EXPECT_TRUE(___PROCEDUREP(___SELF))) GB_JUMP_CALL(___LABEL_ENTRY_GET(___SELF)) ___ps->temp1=___SELF;___JUMPEXTPRM(___NOTHING,___ps->handler_not_proc)}
#define ___JUMPGLOSAFE(nargs,i,glo) {nargs ___SELF=___GLO(i,glo); if (___EXPECT_TRUE(___PROCEDUREP(___SELF))) GB_JUMP_CALL(___LABEL_ENTRY_GET(___SELF)) ___ps->temp4=(___WORD)&___GLOSTRUCT(i,glo);___JUMPEXTPRM(___NOTHING,___ps->handler_not_proc_glo)}
#endif
#endif
'''
                cfile.write_text(content.replace(boundary, boundary + definitions))
            if expansion_hook:
                scm = cfile.with_suffix(".scm")
                scm_hash = hashlib.sha256(scm.read_bytes()).hexdigest()
                invoke(f"expand-{stem}", [str(home / "bin/gsc"), "-c", "-track-scheme", "-o", str(cfile),
                                          *expansion_prelude, str(scm)])
                if hashlib.sha256(scm.read_bytes()).hexdigest() != scm_hash:
                    raise RuntimeError("original Scheme input changed")
                matches = re.findall(r"^STRUCTURE-EXPANSIONS (\d+)$",
                                     (output / f"expand-{stem}.log").read_text(), re.MULTILINE)
                if len(matches) != 1 or cfile.stat().st_size > 6 * 1024 * 1024:
                    raise RuntimeError("primitive expansion marker or six-MiB C budget failed")
                expansion_count = int(matches[0])
            if args.bridge_hot_edges:
                peers = {
                    "gerbil/runtime/hash": ("gerbil/runtime/table",),
                    "gerbil/runtime/table": ("gerbil/expander/core",),
                    "gerbil/expander/core": ("gerbil/runtime/hash", "gerbil/expander/stx"),
                    "gerbil/expander/stx": ("gerbil/expander/core", "gerbil/runtime/util"),
                    "gerbil/runtime/util": ("gerbil/expander/stx",),
                    "gerbil/runtime/mop": ("gerbil/runtime/interface",),
                    "gerbil/runtime/interface": ("gerbil/runtime/mop", "gerbil/runtime/hash"),
                }.get(mod, ())
                prefix = "".join(f"#define GB_BRIDGE_HOT{i} ___H_{peer.replace('/', '____')}\n"
                                 for i, peer in enumerate(peers, 1))
                content = cfile.read_text()
                if content.count("#undef ___MD_ALL") != 1:
                    raise RuntimeError("unique generated module boundary required")
                cfile.write_text(content.replace("#undef ___MD_ALL", prefix + "#undef ___MD_ALL"))
            if structure_probe:
                content = cfile.read_text()
                if content.count("#undef ___MD_ALL") != 1:
                    raise RuntimeError("unique generated module boundary required")
                cfile.write_text(content.replace("#undef ___MD_ALL",
                    f"#include {json.dumps(str(structure_header))}\n#undef ___MD_ALL"))
            if args.host_count_probe:
                content = cfile.read_text()
                if content.count("#undef ___MD_ALL") != 1:
                    raise RuntimeError("unique generated module boundary required")
                probe = r'''
#if defined(__APPLE__) && defined(__GNUC__) && !defined(__clang__)
#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/mman.h>
static volatile uint64_t *gambit_host_count;
static void __attribute__((constructor)) gambit_host_count_init(void) {
  const char *dir = getenv("GAMBIT_HOST_COUNT_DIR");
  char path[4096];
  int fd;
  void *mapped;
  if (!dir) return;
  if (snprintf(path, sizeof(path), "%s/%ld-MODULE.counter", dir,
               (long)getpid()) >= sizeof(path)) abort();
  fd = open(path, O_RDWR | O_CREAT | O_EXCL, 0600);
  if (fd < 0 || ftruncate(fd, sizeof(uint64_t))) abort();
  mapped = mmap(0, sizeof(uint64_t), PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
  close(fd);
  if (mapped == MAP_FAILED) abort();
  gambit_host_count = mapped;
}
#undef ___REGISTER_HOST_ENTRY
#define ___REGISTER_HOST_ENTRY \
  do { if (gambit_host_count) ++*gambit_host_count; } while (0);
#endif
'''.replace("MODULE", stem)
                cfile.write_text(content.replace("#undef ___MD_ALL", probe + "\n#undef ___MD_ALL"))
            if args.distributed_host_exit:
                content = cfile.read_text()
                if content.count("#undef ___MD_ALL") != 1:
                    raise RuntimeError("unique generated module boundary required")
                # Distinct zero-instruction asm operands retain branch-site identity.
                exits = r'''
#if defined(__APPLE__) && defined(__GNUC__) && !defined(__clang__) && \
    defined(___SINGLE_HOST) && defined(___INLINE_JUMPS) && \
    defined(___USE_PROPER_TAIL_CALL_EXCLUSIVELY_TO_EXIT_HOST)
#define GAMBIT_DARWIN_LOCAL_EXIT(dest) do { \
  ___pc = (dest); \
  ___ps->pc = ___pc; \
  ___W_ALL \
  __asm__ __volatile__("" : : "i" (__COUNTER__) : "memory"); \
  ___TAIL_CALL_VOID(___CALL_LABEL_HOST(___pc, ___ps)); \
} while (0)
#undef ___JUMPEXT
#define ___JUMPEXT(dest) { GAMBIT_DARWIN_LOCAL_EXIT(dest); }
#undef ___JUMPFAST
#define ___JUMPFAST(dest) { \
  ___pc = (dest); \
  if (___EXPECT_FALSE(___LABEL_HOST_GET(___pc) != ___HOST_PROC)) { \
    GAMBIT_DARWIN_LOCAL_EXIT(___pc); \
  } \
  goto *___LABEL_HOST_LABEL_GET(___pc); \
}
#endif
'''
                cfile.write_text(content.replace("#undef ___MD_ALL", exits + "\n#undef ___MD_ALL"))
            if args.private_register_bridge:
                content = cfile.read_text()
                required = "#define ___MD_ALL ___D_HEAP ___D_FP ___D_R0 ___D_R1 ___D_R2 ___D_R3 ___D_R4"
                reads = "#define ___MR_ALL ___R_HEAP ___R_FP ___R_R0 ___R_R1 ___R_R2 ___R_R3 ___R_R4"
                writes = "#define ___MW_ALL ___W_HEAP ___W_FP ___W_R0 ___W_R1 ___W_R2 ___W_R3 ___W_R4"
                if content.count("#undef ___MD_ALL") != 1 or any(
                        requirement not in content for requirement in (required, reads, writes)):
                    raise RuntimeError("bridge requires unique host boundary and all five declared registers")
                cfile.write_text(content.replace("#undef ___MD_ALL",
                    f"#include {json.dumps(str(bridge_header))}\n#undef ___MD_ALL"))
            if mod in pc_sources:
                if cfile.read_text() != (home / "lib/static" / cfile.name).read_text():
                    raise RuntimeError("separate PC landmarks require unchanged original C")
                cfile.write_text(pc_sources[mod])
            e = dict(env)
            e.update(GAMBITDIR_INCLUDE=str(chome / "include"), GAMBITDIR_LIB=str(chome / "lib"),
                     BUILD_OBJ_INPUT_FILENAMES_PARAM=str(cfile),
                     BUILD_OBJ_OUTPUT_FILENAME_PARAM=str(obj),
                     BUILD_OBJ_CC_OPTIONS_PARAM=f"{options} -g", BUILD_OBJ_META_INFO_FILE_PARAM=str(cfile))
            before = hashlib.sha256(cfile.read_bytes()).hexdigest()
            elapsed = invoke(f"compile-{stem}", [str(builder), "obj"], e)
            if hashlib.sha256(cfile.read_bytes()).hexdigest() != before:
                raise RuntimeError("generated C changed during object-only experiment")
            return {"module": mod, "generatedCSha256": before,
                    "restRegisterCallsites": rest_sites,
                    "primitiveExpansions": expansion_count,
                    "originalGeneratedCSha256": original_hash, "wallSeconds": elapsed,
                    "objectSha256": hashlib.sha256(obj.read_bytes()).hexdigest()}

        diagnostic = args.host_count_probe or args.bridge_edge_probe or args.structure_instance_count or args.primitive_call_count or args.host_exit_count or args.kernel_label_count or args.return_label_count or args.gen_entry_count or args.native_structure_jump_count or args.guarded_trace_count or args.native_pc_symbols or args.small_hash_scan_count
        report["diagnosticOnly"] = diagnostic
        report["moduleLocalGlobalTable"] = args.module_local_global_table
        report["externalCallLayout"] = args.external_call_layout
        print(f"RUNTIME-PROFILE {len(selected)} C units, diagnostic={diagnostic}, capacity {cores}", flush=True)
        if args.coalesce_original_hosts:
            for mod in selected:
                cfile = static / (mod.replace("/", "__") + ".c")
                report["objects"].append({"module": mod, "reusedOriginalObject": True,
                    "generatedCSha256": hashlib.sha256(cfile.read_bytes()).hexdigest(),
                    "objectSha256": hashlib.sha256(cfile.with_suffix(".o").read_bytes()).hexdigest()})
            save()
        else:
            with ThreadPoolExecutor(max_workers=cores) as pool:
                futures = [pool.submit(compile_object, mod) for mod in selected]
                for future in as_completed(futures):
                    row = future.result()
                    report["objects"].append(row)
                    save()
                    print(f"OBJECT-OK {row['module']}: {row['wallSeconds']:.3f}s", flush=True)
        cfiles = [static / (mod.replace("/", "__") + ".c") for mod in [*modules, "gerbil/main"]]
        link = output / "gerbil-link.c"
        invoke("generate-link", [str(home / "bin/gsc"), "-link", "-track-scheme",
                                 "-o", str(link), *map(str, cfiles)])
        if args.coalesce_original_hosts:
            excluded = set(args.coalesce_exclude)
            if not excluded.issubset(selected) or excluded == set(selected):
                raise RuntimeError("exclusions must be a proper subset of selected original modules")
            selected_files = [path for path in cfiles if path.stem.replace("__", "/") in selected
                              and path.stem.replace("__", "/") not in excluded]
            report["coalescedExcludedOriginalModules"] = sorted(excluded)
            runtime_linkers = ()
            if args.coalesce_kernel:
                kernel = candidate / "src/gambit/lib/_kernel.c"
                selected_files.insert(0, kernel)
                runtime_linkers = ("___LNK___kernel",)
                report["originalKernelGeneratedCSha256"] = hashlib.sha256(kernel.read_bytes()).hexdigest()
            content, details = render_coalesced_hosts(selected_files, link.read_text(), output, runtime_linkers,
                                                     args.guarded_global_jumps, args.return_label_count,
                                                     args.local_return_guards, args.cache_label_bases, args.gen_entry_count,
                                                     args.vector_entry_guards, args.guarded_leaf_clones,
                                                     args.internal_leaf_clones, args.known_return_guards,
                                                     args.local_subroutine_clones, args.defer_local_frames,
                                                     args.guarded_readonly_traces, args.guarded_trace_polls,
                                                     args.guarded_trace_restart_polls,
                                                     args.guarded_trace_coalesce_polls,
                                                     args.guarded_trace_primitive_boundary,
                                                     args.guarded_trace_epoch_cache,
                                                     args.guarded_trace_inline_lookup,
                                                     args.guarded_trace_outline_lookup,
                                                     args.parameter_entry_fastpath,
                                                     args.guarded_trace_allocations,
                                                     args.parameter_identity_return,
                                                     args.parameter_env_lookup,
                                                     args.bounded_primitive_entries,
                                                     args.guarded_trace_lookup_return_branches,
                                                     args.supplementary_pure_branches,
                                                     args.supplementary_fresh_branches,
                                                     args.scalar_caller_label, args.scalar_boundary_label)
            if args.scalar_boundary_label:
                if len(details.get('scalarBoundaryTrees', [])) != len(args.scalar_boundary_label):
                    raise RuntimeError('not all requested scalar boundaries were emitted')
                report['scalarBoundaryLabels'] = args.scalar_boundary_label
                report['scalarBoundaryGeneratorSha256'] = hashlib.sha256(
                    Path(__file__).with_name('gambit_scalar_boundary.py').read_bytes()).hexdigest()
                report['scalarEscapeGeneratorSha256'] = hashlib.sha256(
                    Path(__file__).with_name('gambit_fresh_escape.py').read_bytes()).hexdigest()
            if args.scalar_caller_label:
                if len(details.get('scalarCallerTrees', [])) != len(args.scalar_caller_label):
                    raise RuntimeError('not all requested scalar callers were emitted')
                report['scalarCallerLabels'] = args.scalar_caller_label
                report['scalarCallerGeneratorSha256'] = hashlib.sha256(
                    Path(__file__).with_name('gambit_scalar_caller.py').read_bytes()).hexdigest()
                report['scalarEscapeGeneratorSha256'] = hashlib.sha256(
                    Path(__file__).with_name('gambit_fresh_escape.py').read_bytes()).hexdigest()
            if args.supplementary_pure_branches or args.supplementary_fresh_branches:
                if not details.get('supplementaryPureTrees'):
                    raise RuntimeError('supplementary tree candidate has no static coverage')
                report['pureTreeGeneratorSha256'] = hashlib.sha256(
                    Path(__file__).with_name('gambit_trace_tree.py').read_bytes()).hexdigest()
            if args.bounded_primitive_entries:
                report['boundedPrimitiveEntries'] = True
                report['boundedPrimitiveGeneratorSha256'] = hashlib.sha256(
                    Path(__file__).with_name('gambit_bounded_primitives.py').read_bytes()).hexdigest()
            if args.guarded_trace_outline_lookup:
                report["nativeTraceHelperOptimization"] = "O3"
                report["nativeTraceHelperGeneratorSha256"] = hashlib.sha256(
                    Path(__file__).with_name("gambit_trace_outlining.py").read_bytes()).hexdigest()
            if args.parameter_entry_fastpath:
                report['parameterIdentityReturn'] = args.parameter_identity_return
                report['parameterEnvLookup'] = args.parameter_env_lookup
                report["parameterEntryGeneratorSha256"] = hashlib.sha256(
                    Path(__file__).with_name("gambit_parameter_entry.py").read_bytes()).hexdigest()
            if args.guarded_readonly_traces:
                if not details.get("guardedReadOnlyTraces"):
                    raise RuntimeError("readonly trace candidate has no actual static coverage")
                report["guardedTraceGeneratorSha256"] = hashlib.sha256(
                    Path(__file__).with_name("gambit_guarded_trace.py").read_bytes()).hexdigest()
                if args.guarded_trace_epoch_cache:
                    report["epochCacheGeneratorSha256"] = hashlib.sha256(
                        Path(__file__).with_name("gambit_trace_epoch_cache.py").read_bytes()).hexdigest()
                if args.guarded_trace_count:
                    report["traceCountColumns"] = ["site", "attempts", "successes", "cachedPrefixes"]
                    report["traceGuardMissColumns"] = ["site", "guard", "count"]
                    content = '''#include <stdio.h>
#include <stdlib.h>
static unsigned long gb_trace_attempts[256], gb_trace_successes[256], gb_trace_cached[256];
static unsigned long gb_pure_entries[256], gb_pure_hits[256];
static unsigned long gb_fresh_commits[256], gb_fresh_words[256], gb_fresh_rollbacks[256];
static unsigned long gb_scalar_elided_words;
static unsigned long gb_trace_guard_misses[256][64];
static unsigned long gb_trace_stale[65536], gb_trace_collisions[256];
static unsigned gb_trace_last_mutation;
#define GB_TRACE_ENTRY(site) (++gb_trace_attempts[site])
#define GB_TRACE_HIT(site) (++gb_trace_successes[site])
#define GB_PURE_TREE_ENTRY(site) (++gb_pure_entries[site])
#define GB_PURE_TREE_HIT(site) (++gb_pure_hits[site])
#define GB_FRESH_TREE_COMMIT(site,words) do { ++gb_fresh_commits[site]; gb_fresh_words[site]+=(words); } while (0)
#define GB_FRESH_TREE_ROLLBACK(site,words) (gb_fresh_rollbacks[site]+=(words))
#define GB_SCALAR_ELIDED_WORDS(words) (gb_scalar_elided_words+=(words))
#define GB_TRACE_GUARD_MISS(site,guard) (++gb_trace_guard_misses[site][guard])
#define GB_TRACE_CACHE_SITE(site) (++gb_trace_cached[site])
#define GB_TRACE_FENCE_SITE(site) (gb_trace_last_mutation=(site))
#define GB_TRACE_CACHE_MISS(site,stale) do { if (stale) ++gb_trace_stale[gb_trace_last_mutation]; else ++gb_trace_collisions[site]; } while (0)
#define GB_TRACE_THREAD_CACHE_MISS(site) (++gb_trace_stale[65535])
static void __attribute__((destructor)) gb_trace_counts_dump(void) {
  const char *path=getenv("GAMBIT_TRACE_COUNT_FILE");
  if (path) {
    FILE *file=fopen(path,"w");
    if (file) {
      for (int site=0; site<256; ++site)
        if (gb_trace_attempts[site]) fprintf(file,"%d %lu %lu %lu\\n",site,gb_trace_attempts[site],gb_trace_successes[site],gb_trace_cached[site]);
      fclose(file);
    }
    char guards[4096];
    if (snprintf(guards,sizeof(guards),"%s.pure-trees",path)<sizeof(guards)) {
      file=fopen(guards,"w");
      if (file) {
        for (int site=0; site<256; ++site)
          if (gb_pure_entries[site]) fprintf(file,"%d %lu %lu\\n",site,gb_pure_entries[site],gb_pure_hits[site]);
        fclose(file);
      }
    }
    if (snprintf(guards,sizeof(guards),"%s.fresh-trees",path)<sizeof(guards)) {
      file=fopen(guards,"w");
      if (file) {
        for (int site=0; site<256; ++site)
          if (gb_pure_entries[site]) fprintf(file,"%d %lu %lu %lu\\n",site,gb_fresh_commits[site],gb_fresh_words[site],gb_fresh_rollbacks[site]);
        fclose(file);
      }
    }
    if (snprintf(guards,sizeof(guards),"%s.scalar-elided-words",path)<sizeof(guards)) {
      file=fopen(guards,"w");
      if (file) { fprintf(file,"%lu\\n",gb_scalar_elided_words); fclose(file); }
    }
    if (snprintf(guards,sizeof(guards),"%s.guards",path)<sizeof(guards)) {
      file=fopen(guards,"w");
      if (file) {
        for (int site=0; site<256; ++site)
          for (int guard=0; guard<64; ++guard)
            if (gb_trace_guard_misses[site][guard])
              fprintf(file,"%d %d %lu\\n",site,guard,gb_trace_guard_misses[site][guard]);
        fclose(file);
      }
    }
    char reasons[4096];
    if (snprintf(reasons,sizeof(reasons),"%s.mutation-reasons",path)<sizeof(reasons)) {
      file=fopen(reasons,"w");
      if (file) {
        for (int reason=0; reason<65536; ++reason)
          if (gb_trace_stale[reason]) fprintf(file,"%d %lu\\n",reason,gb_trace_stale[reason]);
        for (int site=0; site<256; ++site)
          if (gb_trace_collisions[site]) fprintf(file,"collision-%d %lu\\n",site,gb_trace_collisions[site]);
        fclose(file);
      }
    }
  }
}
''' + content
                    if args.parameter_entry_fastpath:
                        report['parameterCountFields'] = ['hits', 'identity', 'slots', 'environment']
                        content = '''#include <stdio.h>
#include <stdlib.h>
static unsigned long gb_parameter_count_hits, gb_parameter_count_identity;
static unsigned long gb_parameter_count_slots[4], gb_parameter_count_env[2];
#define GB_PARAMETER_HIT() (++gb_parameter_count_hits)
#define GB_PARAMETER_IDENTITY_HIT() (++gb_parameter_count_identity)
#define GB_PARAMETER_SLOT(slot) (++gb_parameter_count_slots[slot])
#define GB_PARAMETER_ENV_HIT(bound) (++gb_parameter_count_env[bound])
static void __attribute__((destructor)) gb_parameter_count_dump(void) {
  const char *path=getenv("GAMBIT_TRACE_COUNT_FILE");
  char name[4096];
  if (path && snprintf(name,sizeof(name),"%s.parameters",path)<sizeof(name)) {
    FILE *file=fopen(name,"w");
    if (file) {
      fprintf(file,"{\\"hits\\":%lu,\\"identity\\":%lu,\\"slots\\":[%lu,%lu,%lu],\\"environment\\":[%lu,%lu]}\\n",
        gb_parameter_count_hits,gb_parameter_count_identity,gb_parameter_count_slots[1],
        gb_parameter_count_slots[2],gb_parameter_count_slots[3],gb_parameter_count_env[0],gb_parameter_count_env[1]);
      fclose(file);
    }
  }
}
''' + content
            if args.bounded_primitive_entries and args.guarded_trace_count:
                report['boundedPrimitiveCountFields'] = ['length', 'reverse', 'structure', 'reversePairs']
                content = '''#include <stdio.h>
#include <stdlib.h>
static unsigned long gb_bounded_counts[3],gb_bounded_reverse_pairs;
#define GB_BOUNDED_PRIMITIVE_HIT(kind,size) do { ++gb_bounded_counts[kind]; if ((kind)==1) gb_bounded_reverse_pairs+=(size); } while (0)
static void __attribute__((destructor)) gb_bounded_count_dump(void) {
  const char *path=getenv("GAMBIT_TRACE_COUNT_FILE");
  char name[4096];
  if (path && snprintf(name,sizeof(name),"%s.primitives",path)<sizeof(name)) {
    FILE *file=fopen(name,"w");
    if (file) {
      fprintf(file,"{\\"length\\":%lu,\\"reverse\\":%lu,\\"structure\\":%lu,\\"reversePairs\\":%lu}\\n",
        gb_bounded_counts[0],gb_bounded_counts[1],gb_bounded_counts[2],gb_bounded_reverse_pairs);
      fclose(file);
    }
  }
}
''' + content
            if args.small_hash_scan:
                scan = Path(__file__).with_name('gambit-small-hash-scan.h').read_text()
                report['smallHashScanHeaderSha256'] = hashlib.sha256(scan.encode()).hexdigest()
                report['smallHashScan'] = dict(maximumSlots=8, counted=args.small_hash_scan_count,
                                              performanceQualified=False)
                if args.small_hash_scan_count:
                    scan = '''#include <stdio.h>
#include <stdlib.h>
static unsigned long gb_hash_entries,gb_hash_selected,gb_hash_hits,gb_hash_misses;
static unsigned long gb_hash_sizes[5];
#define GB_HASH_SCAN_ENTRY() (++gb_hash_entries)
#define GB_HASH_SCAN_SELECTED(slots) (++gb_hash_selected)
#define GB_HASH_SCAN_HIT() (++gb_hash_hits)
#define GB_HASH_SCAN_MISS() (++gb_hash_misses)
#define GB_HASH_SCAN_SIZE(slots) (++gb_hash_sizes[(slots)<=8?0:(slots)<=32?1:(slots)<=128?2:(slots)<=512?3:4])
static void __attribute__((destructor)) gb_hash_scan_dump(void) {
  const char *path=getenv("GAMBIT_TRACE_COUNT_FILE");
  char name[4096];
  if (path && snprintf(name,sizeof(name),"%s.hash-scan",path)<sizeof(name)) {
    FILE *file=fopen(name,"w");
    if (file) {
      fprintf(file,"%lu %lu %lu %lu %lu %lu %lu %lu %lu\\n",
        gb_hash_entries,gb_hash_selected,gb_hash_hits,gb_hash_misses,
        gb_hash_sizes[0],gb_hash_sizes[1],gb_hash_sizes[2],gb_hash_sizes[3],gb_hash_sizes[4]);
      fclose(file);
    }
  }
}
''' + scan
                boundary = '#include "gambit.h"'
                if content.count(boundary) != 1:
                    raise RuntimeError('small hash scan requires a unique Gambit header boundary')
                content = content.replace(boundary, boundary+'\n'+scan, 1)
            if args.native_pc_symbols:
                from gambit_pc_symbols import inject as inject_pc_symbols
                content, landmarks = inject_pc_symbols(content)
                (output / "pc-landmarks.json").write_text(json.dumps(landmarks, indent=2) + "\n")
                report["nativePcLandmarks"] = len(landmarks)
                report["nativePcGeneratorSha256"] = hashlib.sha256(
                    Path(__file__).with_name("gambit_pc_symbols.py").read_bytes()).hexdigest()
            if len(content.encode()) > 24 * 1024 * 1024:
                raise RuntimeError("coalesced translation unit exceeded 24-MiB diagnostic budget")
            link.write_text(content)
            report.update(details)
            if args.guarded_trace_lookup_return_branches:
                report['typeChainGeneratorSha256'] = hashlib.sha256(
                    Path(__file__).with_name('gambit_type_chain.py').read_bytes()).hexdigest()
            if args.guarded_trace_lookup_return_branches and not any(
                    site['terminal'] == 'GB_ORIGINAL_REENTRY' for site in details['guardedReadOnlyTraces']):
                raise RuntimeError('lookup return branch candidate lacks actual static reentry')
            report["coalescedLinkBytes"] = link.stat().st_size
            report["coalescingGeneratorSha256"] = hashlib.sha256(
                Path(__file__).with_name("gambit_host_coalescing.py").read_bytes()).hexdigest()
            save()
        e = dict(env)
        e.update(GAMBITDIR_INCLUDE=str(chome / "include"), GAMBITDIR_LIB=str(chome / "lib"),
                 BUILD_OBJ_INPUT_FILENAMES_PARAM=str(link),
                 BUILD_OBJ_OUTPUT_FILENAME_PARAM=str(link.with_suffix(".o")),
                 BUILD_OBJ_META_INFO_FILE_PARAM=str(link))
        if args.coalesce_kernel:
            e["BUILD_OBJ_CC_OPTIONS_PARAM"] = f'-DHAVE_CONFIG_H -I{candidate / "src/gambit/lib"} -I{candidate / "src/gambit/include"}'
        invoke("compile-link", [str(builder), "obj"], e)
        objects = [path.with_suffix(".o") for path in cfiles]
        if args.kernel_label_count:
            kernel = candidate / f"src/gambit/lib/_{args.runtime_label_unit}.c"
            original = kernel.read_text()
            if original.count("___BEGIN_M_COD\n") != 1:
                raise RuntimeError("unique original kernel host required")
            header = output / "gambit-kernel-label-count.h"
            header.write_bytes(Path(__file__).with_name(header.name).read_bytes())
            counted = output / "kernel-label-count.c"
            counted.write_text(original.replace("___BEGIN_M_COD\n", f'#include {json.dumps(str(header))}\n___BEGIN_M_COD\n'))
            report["originalKernelGeneratedCSha256"] = hashlib.sha256(kernel.read_bytes()).hexdigest()
            report["runtimeLabelUnit"] = args.runtime_label_unit
            report["kernelLabelCounterSha256"] = hashlib.sha256(header.read_bytes()).hexdigest()
            e = dict(env)
            e.update(GAMBITDIR_INCLUDE=str(chome / "include"), GAMBITDIR_LIB=str(chome / "lib"),
                     BUILD_OBJ_INPUT_FILENAMES_PARAM=str(counted),
                     BUILD_OBJ_OUTPUT_FILENAME_PARAM=str(counted.with_suffix(".o")),
                     BUILD_OBJ_META_INFO_FILE_PARAM=str(counted),
                     BUILD_OBJ_CC_OPTIONS_PARAM=f'-D___LIBRARY -DHAVE_CONFIG_H -I{candidate / "src/gambit/lib"} -I{candidate / "src/gambit/include"}')
            invoke("compile-kernel-label-count", [str(builder), "obj"], e)
            objects.append(counted.with_suffix(".o"))
        if args.private_register_bridge:
            bridge = output / ("gambit-fixed-gvm-bridge.c" if args.fixed_gvm_registers
                               else "gambit-private-register-bridge.c")
            bridge.write_bytes(Path(__file__).with_name(bridge.name).read_bytes())
            report["privateBridgeSourceSha256"] = hashlib.sha256(bridge.read_bytes()).hexdigest()
            bridge_object = output / "gambit-private-register-bridge.o"
            e = dict(env)
            e.update(GAMBITDIR_INCLUDE=str(chome / "include"), GAMBITDIR_LIB=str(chome / "lib"),
                     BUILD_OBJ_INPUT_FILENAMES_PARAM=str(bridge),
                     BUILD_OBJ_OUTPUT_FILENAME_PARAM=str(bridge_object),
                     BUILD_OBJ_CC_OPTIONS_PARAM="-DGB_BRIDGE_EDGE_PROBE" if args.bridge_edge_probe else "",
                     BUILD_OBJ_META_INFO_FILE_PARAM=str(bridge))
            invoke("compile-private-bridge", [str(builder), "obj"], e)
            objects.append(bridge_object)
        invoke("link-bach", [env["CC"], "-o", str(chome / "bin/gerbil"),
                             *map(str, objects), str(link.with_suffix(".o")),
                             f"-L{chome / 'lib'}", "-lgambit", "-ldl", "-lm"])
        e = dict(env)
        e.update(GERBIL_HOME=str(home), GERBIL_LOADPATH=str(home / "lib"),
                 GAMBOPT=f"~~bin={home / 'bin'},~~lib={home / 'lib'},~~include={home / 'include'}",
                 PATH=f"{chome / 'bin'}:{env['PATH']}")
        invoke("import-smoke", [str(chome / "bin/gxi"), "-e",
                               '(import :std/make :std/test :std/build-script) (displayln "IMPORT-OK")'], e)
        if not (output / "import-smoke.log").read_text().rstrip().endswith("IMPORT-OK"):
            raise RuntimeError("native import smoke failed")
        report["binaryHashes"] = {name: hashlib.sha256((chome / "bin" / name).read_bytes()).hexdigest()
                                  for name in ("gxi", "gsc")}
        report["gscUnchanged"] = report["binaryHashes"]["gsc"] == hashlib.sha256((home / "bin/gsc").read_bytes()).hexdigest()
        report["qualified"] = True
    except BaseException as error:
        report["failure"] = str(error)
        raise
    finally:
        report["hostLoadEnd"] = os.getloadavg()
        save()


if __name__ == "__main__":
    main()
