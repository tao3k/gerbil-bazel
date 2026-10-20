#!/usr/bin/env python3
"""Probe Gambit compilation-unit boundaries without editing Gerbil inputs."""
import argparse
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--scope", choices=("expander-hot", "expander", "runtime-expander", "runtime-object", "runtime-table-object"), default="expander-hot")
    parser.add_argument("--inlining-limit", type=int)
    parser.add_argument("--structure-instance-inline", action="store_true")
    parser.add_argument("--object-source", type=Path)
    parser.add_argument("--prior-bundle", type=Path)
    args = parser.parse_args()
    if args.inlining_limit is not None and not 370 <= args.inlining_limit <= 1000:
        parser.error("bounded inlining diagnostic requires 370..1000")
    repo = Path(__file__).resolve().parents[3]
    baseline, output = args.baseline.resolve(), args.output.resolve()
    if platform.system() != "Darwin" or not output.is_relative_to(repo / ".data"):
        parser.error("Darwin-only isolated experiment under .data required")
    output.mkdir(parents=True, exist_ok=False)
    env = build_environment()
    macros = subprocess.check_output([env["CC"], "-dM", "-E", "-x", "c", os.devnull],
                                     env=env, text=True)
    if "#define __clang__" in macros or "#define __GNUC__ 16\n" not in macros:
        raise RuntimeError("real GNU GCC 16 required")
    home = baseline / "build"
    env.pop("GERBIL_BUILD_PREFIX", None)
    env.pop("GAMBIT_HOST_GROUP_BUDGET", None)
    env.update(GERBIL_HOME=str(home), GERBIL_PATH=str(output / "empty-user"),
               GERBIL_LOADPATH=str(home / "lib"), GERBIL_GSC=str(home / "bin/gsc"),
               GAMBOPT=f"~~bin={home / 'bin'},~~lib={home / 'lib'},~~include={home / 'include'}",
               PATH=f"{home / 'bin'}:{env['PATH']}")
    report = {"qualified": False, "performanceQualified": False,
              "scope": "Gambit-compilation-unit-prototype", "sourceEdits": False,
              "initializationOrderChanged": False, "hostLoadStart": os.getloadavg(),
              "steps": []}

    def save():
        (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")

    def invoke(name, argv, process_env=None):
        started = time.monotonic()
        with (output / f"{name}.log").open("w") as log:
            child = subprocess.Popen(argv, env=process_env or env, stdout=log,
                                     stderr=subprocess.STDOUT, start_new_session=True)
            try:
                while child.poll() is None:
                    try:
                        child.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        print(f"ACTIVE {name}: {time.monotonic() - started:.1f}s pid={child.pid}", flush=True)
                    if time.monotonic() - started > 180:
                        raise TimeoutError(f"{name} exceeded 180 seconds")
            finally:
                if child.poll() is None:
                    os.killpg(child.pid, signal.SIGTERM)
                    try:
                        child.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        os.killpg(child.pid, signal.SIGKILL)
                        child.wait()
        report["steps"].append({"name": name, "exitCode": child.returncode,
                                "wallSeconds": time.monotonic() - started})
        save()
        if child.returncode:
            raise RuntimeError(f"{name} failed; inspect retained log")
        print(f"OK {name}: {time.monotonic() - started:.3f}s", flush=True)

    try:
        script = baseline / "src/build/build-bach.ss"
        expression = ('(import :std/encoding/json) '
                      f'(call-with-input-file {json.dumps(str(script))} '
                      '(lambda (p) (let lp () (let (f (read p)) '
                      '(cond ((eof-object? f) (error "builtin list missing")) '
                      '((and (pair? f) (eq? (car f) \'def) '
                      '(eq? (cadr f) \'builtin-modules)) '
                      '(displayln (json->string (list->vector (cadr (caddr f)))))) '
                      '(else (lp)))))))')
        invoke("module-order", [str(home / "bin/gxi"), "-e", expression])
        modules = json.loads((output / "module-order.log").read_text().splitlines()[-1])
        selected = ["gerbil/expander/common", "gerbil/expander/stx",
                    "gerbil/expander/core", "gerbil/expander/top"]
        if args.scope == "runtime-expander":
            selected = modules[:modules.index("gerbil/expander") + 1]
        elif args.scope == "expander":
            selected = modules[modules.index("gerbil/expander/common"):modules.index("gerbil/expander") + 1]
        elif args.scope == "runtime-object":
            selected = modules[modules.index("gerbil/runtime/mop"):modules.index("gerbil/runtime/hash") + 1]
        elif args.scope == "runtime-table-object":
            selected = modules[modules.index("gerbil/runtime/table"):modules.index("gerbil/runtime/hash") + 1]
        start = modules.index(selected[0])
        if modules[start:start + len(selected)] != selected:
            raise RuntimeError("selected modules are not contiguous in official order")
        report["selectedModules"] = selected
        report["bundleScope"] = args.scope
        report["inliningLimit"] = args.inlining_limit
        inputs = [home / "lib/static" / (mod.replace("/", "__") + ".scm") for mod in selected]
        report["inputHashes"] = {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in inputs}
        candidate = output / "source"
        invoke("clone-toolchain", ["/bin/cp", "-cR", str(baseline), str(candidate)])
        chome = candidate / "build"
        # Gambit's linker expects the C linker ID to match the final supplied name.
        bundle = output / (selected[-1].replace("/", "__") + ".scm")
        # Supply aliases preserve Gambit's registry; includes preserve exact forms/order.
        declarations = ([f"(declare (inlining-limit {args.inlining_limit}))"]
                        if args.inlining_limit is not None else [])
        bundle.write_text("\n".join(
            declarations + [f"(##supply-module {mod.replace('/', '__')})" for mod in selected]
            + [f"(include {json.dumps(str(path))})" for path in inputs]) + "\n")
        cfile = bundle.with_suffix(".c")
        invoke("runtime-smp", [str(home / "bin/gxi"), "-e",
                               '(displayln (if (gerbil-runtime-smp?) "yes" "no"))'])
        smp = (output / "runtime-smp.log").read_text().strip() == "yes"
        prelude = (["-e", "(define-cond-expand-feature|enable-smp|)"] if smp else [])
        prelude += ["-e", f'(include {json.dumps(str(home / "lib/_gambit#.scm"))})']
        report["runtimeSmp"] = smp
        invoke("gambit-compile", [str(home / "bin/gsc"), "-c", "-track-scheme",
                                  "-o", str(cfile), *prelude, str(bundle)])
        if report["inputHashes"] != {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                                     for path in inputs}:
            raise RuntimeError("original generated input changed")
        report["bundleCBytes"] = cfile.stat().st_size
        if (args.inlining_limit is not None or args.scope == "runtime-table-object") and cfile.stat().st_size > 6 * 1024 * 1024:
            raise RuntimeError("inlining exceeded six-MiB generated-C diagnostic budget")
        report["structureInstanceInline"] = args.structure_instance_inline
        if args.structure_instance_inline:
            header = output / "gambit-structure-instance-probe.h"
            header.write_bytes(Path(__file__).with_name(header.name).read_bytes())
            report["structureProbeHeaderSha256"] = hashlib.sha256(header.read_bytes()).hexdigest()
            content = cfile.read_text()
            if content.count("#undef ___MD_ALL") != 1:
                raise RuntimeError("unique generated module boundary required")
            cfile.write_text(content.replace("#undef ___MD_ALL",
                f"#include {json.dumps(str(header))}\n#undef ___MD_ALL"))
        report["bundleCSha256"] = hashlib.sha256(cfile.read_bytes()).hexdigest()
        def jumps(text):
            return {key: len(re.findall(r"\b" + key + r"\(", text))
                    for key in ("___JUMPINT", "___JUMPGLONOTSAFE", "___JUMPPRM")}
        report["generatedJumpSites"] = {
            "original": jumps("\n".join(path.with_suffix(".c").read_text() for path in inputs)),
            "bundle": jumps(cfile.read_text()),
        }
        builder = home / "bin/gambuild-C"

        def compile_c(name, path):
            e = dict(env)
            e.update(GAMBITDIR_INCLUDE=str(home / "include"), GAMBITDIR_LIB=str(home / "lib"),
                     BUILD_OBJ_INPUT_FILENAMES_PARAM=str(path),
                     BUILD_OBJ_OUTPUT_FILENAME_PARAM=str(path.with_suffix(".o")),
                     BUILD_OBJ_META_INFO_FILE_PARAM=str(path))
            invoke(name, [str(builder), "obj"], e)

        compile_c("gnu-compile-bundle", cfile)
        cfiles = [home / "lib/static" / (mod.replace("/", "__") + ".c")
                  for mod in [*modules, "gerbil/main"]]
        cfiles[start:start + len(selected)] = [cfile]
        bundled_modules = set(selected)
        if args.prior_bundle:
            prior = args.prior_bundle.resolve()
            if not prior.is_relative_to(repo / ".data"):
                raise RuntimeError("prior bundle must stay under project .data")
            prior_report = json.loads((prior / "report.json").read_text())
            if not prior_report.get("qualified") or not prior_report.get("gscUnchanged"):
                raise RuntimeError("prior bundle has not passed its native import/link gates")
            prior_modules = prior_report["selectedModules"]
            if bundled_modules.intersection(prior_modules):
                raise RuntimeError("separate bundles must not overlap")
            for name, digest in prior_report["inputHashes"].items():
                if hashlib.sha256((home / "lib/static" / name).read_bytes()).hexdigest() != digest:
                    raise RuntimeError("prior bundle input differs from baseline")
            prior_c = prior / (prior_modules[-1].replace("/", "__") + ".c")
            first = home / "lib/static" / (prior_modules[0].replace("/", "__") + ".c")
            index = cfiles.index(first)
            expected = [home / "lib/static" / (mod.replace("/", "__") + ".c") for mod in prior_modules]
            if cfiles[index:index + len(prior_modules)] != expected:
                raise RuntimeError("prior module initialization order is not contiguous")
            cfiles[index:index + len(prior_modules)] = [prior_c]
            bundled_modules.update(prior_modules)
            report["priorBundleHashes"] = {
                name: hashlib.sha256((prior / name).read_bytes()).hexdigest()
                for name in ("report.json", prior_c.name, prior_c.with_suffix(".o").name)}
        object_sources = {}
        if args.object_source:
            overlay = args.object_source.resolve() / "build"
            for name in ("bin/gsc", "lib/libgambit.a", "include/gambit.h"):
                if hashlib.sha256((overlay / name).read_bytes()).digest() != hashlib.sha256((home / name).read_bytes()).digest():
                    raise RuntimeError("object overlay changed original compiler/runtime ABI")
            overlay_modules = ("gerbil/expander/core", "gerbil/expander/module",
                "gerbil/expander/compile", "gerbil/expander/stx", "gerbil/expander/stxcase",
                "gerbil/runtime/hash", "gerbil/runtime/table", "gerbil/expander/top",
                "gerbil/runtime/mop", "gerbil/runtime/interface", "gerbil/runtime/util")
            for mod in overlay_modules:
                if mod not in bundled_modules:
                    obj = overlay / "lib/static" / (mod.replace("/", "__") + ".o")
                    object_sources[mod.replace("/", "__") + ".c"] = obj
            report["objectOverlayHashes"] = {name: hashlib.sha256(obj.read_bytes()).hexdigest()
                                             for name, obj in object_sources.items()}
        link = output / "gerbil-link.c"
        invoke("generate-link", [str(home / "bin/gsc"), "-link", "-track-scheme",
                                 "-o", str(link), *map(str, cfiles)])
        compile_c("compile-link", link)
        invoke("link-bach", [env["CC"], "-o", str(chome / "bin/gerbil"),
                             *map(str, [object_sources.get(p.name, p.with_suffix(".o")) for p in cfiles]),
                             str(link.with_suffix(".o")), f"-L{home / 'lib'}", "-lgambit", "-ldl", "-lm"])
        invoke("import-smoke", [str(chome / "bin/gxi"), "-e",
                               '(import :std/make :std/test :std/build-script) (displayln "IMPORT-OK")'])
        if not (output / "import-smoke.log").read_text().rstrip().endswith("IMPORT-OK"):
            raise RuntimeError("import smoke marker missing")
        alias_names = " ".join(mod.replace("/", "__") for mod in modules if mod in bundled_modules)
        invoke("module-aliases", [str(chome / "bin/gxi"), "-e",
                                  "(for-each (lambda (name) "
                                  "(unless (##lookup-registered-module name) "
                                  "(error \"lost Gambit module alias\" name))) "
                                  f"'({alias_names})) (displayln \"ALIASES-OK\")"])
        report["moduleAliasesVerified"] = (output / "module-aliases.log").read_text().rstrip().endswith("ALIASES-OK")
        if not report["moduleAliasesVerified"]:
            raise RuntimeError("module alias marker missing")
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
