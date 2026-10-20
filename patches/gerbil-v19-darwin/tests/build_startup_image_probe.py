#!/usr/bin/env python3
"""Build a read-only Darwin image aggregation experiment, not an install patch."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import signal
import shutil
import subprocess
import time

from bazel_host_environment import build_environment
from run_parser_native_admission_cost import native_admission_prefix, native_admission_expression
from run_mcp_native_cpu_profile import native_admission_receipt_valid
from macho_image_dependencies import dependencies
from audit_startup_gsc_recipe import gsc_recipe_command
from native_object_manifest import text_section


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--syntax-runtime", action="store_true")
    parser.add_argument('--native-admission-project', type=Path)
    parser.add_argument('--native-admission-receipt', type=Path)
    parser.add_argument('--official-tools', action='store_true')
    parser.add_argument('--reuse-units-from', type=Path)
    parser.add_argument('--gambit-macro-inputs', action='store_true')
    parser.add_argument('--original-std-debug-options', action='store_true')
    parser.add_argument('--verify-installed-native-text', action='store_true')
    parser.add_argument('--reuse-known-closure', action='store_true')
    parser.add_argument('--reuse-verified-units-from', type=Path)
    args = parser.parse_args()
    if args.reuse_known_closure and not args.reuse_units_from:
        parser.error('known closure requires its locked complete build receipt')
    if args.verify_installed_native_text and (not args.original_std_debug_options or args.syntax_runtime):
        parser.error('installed native text verification requires original std debug options, no O3 override')
    if args.official_tools and not args.native_admission_project:
        parser.error('official-tool closure requires qualified Native inputs')
    if bool(args.native_admission_project) != bool(args.native_admission_receipt) or (
            args.syntax_runtime and args.native_admission_project):
        parser.error('Native closure requires both isolated project and receipt, no syntax-only mode')
    repo = Path(__file__).resolve().parents[3]
    output = args.output.resolve()
    if platform.system() != "Darwin" or not output.is_relative_to(repo / ".data"):
        parser.error("this experiment is Darwin-only and must stay under project .data")
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
              "scope": "read-only-startup-image-prototype", "cores": cores,
              "hostLoadStart": os.getloadavg(), "units": [],
              "originalStdDebugOptionsUsed": args.original_std_debug_options,
              "installedNativeTextParityProven": False}
    project = None
    reuse_root, reusable = None, {}
    verified_root, verified = None, {}
    if args.native_admission_project:
        project, receipt = args.native_admission_project.resolve(), args.native_admission_receipt.resolve()
        if not all(path.is_relative_to(repo / '.data') for path in (baseline, project, receipt)):
            parser.error('isolated Native inputs required')
        prior = json.loads(receipt.read_text())
        head = subprocess.check_output(['git', '-C', str(project), 'rev-parse', 'HEAD'], text=True).strip()
        if not native_admission_receipt_valid(prior) or head != prior['projectHead'] or any(
                hashlib.sha256((project / name).read_bytes()).hexdigest() != expected
                for name, expected in prior['sourceSha256'].items()):
            parser.error('qualified unchanged Native admission prefix required')
        if hashlib.sha256((home / 'bin/gxi').read_bytes()).hexdigest() != 'cc3b58b627c25c3844249aa752a7773a53d76e319a0212e90a7f28ee46e21928':
            parser.error('unchanged original staging runtime required')
        env.update(GERBIL_PATH=str(project / '.gerbil'),
                   GERBIL_LOADPATH=f"{project / '.gerbil/lib'}:{home / 'lib'}:{project}")
        env['GAMBOPT'] += ',max-heap=1G,debug=q'
        report.update(scope='current-staging-native-preload-image-packing-prototype',
                      projectHead=head, nativeSuiteQualified=False, consumerFlagsChanged=False,
                      runtimeAbiChanged=False, headerSha256=hashlib.sha256((home / 'include/gambit.h').read_bytes()).hexdigest(),
                      rpathSemanticsQualified=False,
                      gscSha256=hashlib.sha256((home / 'bin/gsc').read_bytes()).hexdigest())
        report['officialToolsIncluded'] = args.official_tools
        report['originalGambitMacroInputsUsed'] = args.gambit_macro_inputs
        if args.gambit_macro_inputs:
            report['macroInputSha256'] = hashlib.sha256((home / 'lib/_gambit#.scm').read_bytes()).hexdigest()
    if args.reuse_units_from:
        reuse_root = args.reuse_units_from.resolve()
        if not project or not reuse_root.is_relative_to(repo / '.data'):
            parser.error('isolated qualified Native unit inputs required')
        reuse_report_path = reuse_root / 'report.json'
        reuse_report = json.loads(reuse_report_path.read_text())
        if (reuse_report.get('qualified') is not True
                or reuse_report.get('scope') != report['scope']
                or reuse_report.get('projectHead') != report['projectHead']
                or reuse_report.get('gscSha256') != report['gscSha256']
                or reuse_report.get('headerSha256') != report['headerSha256']
                or reuse_report.get('binaryHashesUnchanged') is not True):
            parser.error('previous complete current-input Native unit build required')
        reusable = {row['path']: row for row in reuse_report['units']}
        report['reusedBuildReceiptSha256'] = hashlib.sha256(reuse_report_path.read_bytes()).hexdigest()
    if args.reuse_verified_units_from:
        verified_root = args.reuse_verified_units_from.resolve()
        if not args.verify_installed_native_text or not verified_root.is_relative_to(repo/'.data'):
            parser.error('partial reuse requires current installed-text verification')
        partial_path = verified_root/'report.json'
        partial = json.loads(partial_path.read_text())
        if (partial.get('scope') != report['scope']
                or partial.get('projectHead') != report['projectHead']
                or partial.get('gscSha256') != report['gscSha256']
                or partial.get('headerSha256') != report['headerSha256']
                or partial.get('macroInputSha256') != report.get('macroInputSha256')
                or partial.get('originalStdDebugOptionsUsed') is not True):
            parser.error('current-input original-debug verified unit receipt required')
        verified = {row['path']: row for row in partial['units']
                    if row.get('installedNativeTextByteExact') is True}
        report['verifiedPartialReceiptSha256'] = hashlib.sha256(partial_path.read_bytes()).hexdigest()

    def save():
        (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")

    def invoke(name, command, cwd=None, process_env=None):
        started = time.monotonic()
        with (output / f"{name}.log").open("w") as log:
            child = subprocess.Popen(command, cwd=cwd, env=process_env or env,
                                     stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            try:
                status = child.wait(timeout=180)
            except subprocess.TimeoutExpired:
                report.setdefault('invocationTimeouts', []).append(
                    dict(name=name, budgetSeconds=180, pid=child.pid))
                save()
                raise
            finally:
                try:
                    os.killpg(child.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
                if child.poll() is None:
                    try:
                        child.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        os.killpg(child.pid, signal.SIGKILL)
                        child.wait()
                try:
                    os.killpg(child.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
        if status:
            raise RuntimeError(f"{name} failed; inspect its retained log")
        return time.monotonic() - started

    try:
        save()
        expression = ('(import :std/make :std/test :std/build-script) '
                      '(def snapshot (list-modules)) (import :std/encoding/json) '
                      '(display "STARTUP-CLOSURE ") (displayln (json->string '
                      '(list->vector (filter-map '
                      '(lambda (kv) (and (string? (cdr kv)) '
                      '(vector (car kv) (cdr kv)))) snapshot))))')
        if project:
            expression = (native_admission_prefix(project)
                          + ('(import :gerbil/tools/gxpkg :std/make :std/build-script) ' if args.official_tools else '')
                          + '(def snapshot (list-modules)) '
                          '(import :std/encoding/json) '
                          '(display "STARTUP-CLOSURE ") (displayln (json->string (list->vector (filter-map '
                          '(lambda (kv) (and (string? (cdr kv)) (vector (car kv) (cdr kv)))) snapshot)))) '
                          '(import :gerbil-parser/t/fixtures/tla-sany-differential/exit-child-process) '
                          '(test-child-process-exit! 0)')
        if args.reuse_known_closure:
            rows = [(row['module'], str(home/row['path'])) for row in reuse_report['units']]
            report['closureReusedFromLockedReceipt'] = True
        else:
            invoke("closure", [str(home / "bin/gxi"), "-e", expression])
            closure_lines = [line.removeprefix('STARTUP-CLOSURE ') for line in
                             (output / 'closure.log').read_text().splitlines() if line.startswith('STARTUP-CLOSURE ')]
            if len(closure_lines) != 1:
                raise RuntimeError('exactly one actual structured startup closure required')
            rows = json.loads(closure_lines[0])
        images = []
        for mod, path in rows:
            native = Path(path).resolve()
            scm = native.with_suffix(".scm")
            if native.is_relative_to(home / "lib") and native.suffix == ".o1" and scm.is_file():
                images.append((mod, native, scm))
        images.sort()
        if args.syntax_runtime:
            images = [item for item in images
                      if item[1].name.endswith("~1.o1")
                      and (item[0].startswith("gerbil/core/") or item[0] == "std/interface~1")]
            report["scope"] = "syntax-phase-runtime-O3-only"
        if len(images) < 2:
            raise RuntimeError("closure has fewer than two independent native images")
        dependency_inventory = {str(native): dependencies(native.read_bytes()) for _, native, _ in images}
        candidate = output / "source"
        if args.syntax_runtime:
            (candidate / "build/lib").mkdir(parents=True)
        else:
            invoke("clone-toolchain", ["/bin/cp", "-cR", str(baseline), str(candidate)])
        work = output / "units"
        work.mkdir()
        script = home / "bin/gambuild-C"

        def compile_unit(index, item):
            mod, native, scm = item
            folder = work / str(index)
            folder.mkdir()
            cfile, obj = folder / "module.c", folder / "module.o"
            module_path = str(scm.relative_to(home / 'lib').with_suffix(''))
            verified_prior = verified.get(str(native.relative_to(home)))
            if verified_prior:
                prior_c = verified_root/'units'/str(verified_prior['index'])/'module.c'
                if (hashlib.sha256(native.read_bytes()).hexdigest() != verified_prior['originalSha256']
                        or hashlib.sha256(scm.read_bytes()).hexdigest() != verified_prior['sourceSha256']
                        or hashlib.sha256(prior_c.read_bytes()).hexdigest() != verified_prior['generatedCSha256']):
                    raise RuntimeError('verified original source or C input changed')
                shutil.copyfile(prior_c, cfile)
                elapsed = 0
            else:
                elapsed = invoke(f"generate-{index}", gsc_recipe_command(home, module_path, cfile,
                                                                         args.gambit_macro_inputs,
                                                                         args.original_std_debug_options))
            generation_log = (verified_root/f"generate-{verified_prior['index']}.log"
                              if verified_prior else output/f'generate-{index}.log')
            if args.gambit_macro_inputs and '*** WARNING -- Variable "macro-' in generation_log.read_text():
                raise RuntimeError('corrected macro recipe still generated an undefined macro')
            if project and re.search(r'__attribute__\s*\(\(\s*(?:constructor|destructor)\b', cfile.read_text()):
                raise RuntimeError('Native packing refuses explicit generated C constructors/destructors')
            e = dict(env)
            e.update(GAMBITDIR_INCLUDE=str(home / "include"), GAMBITDIR_LIB=str(home / "lib"),
                     BUILD_OBJ_INPUT_FILENAMES_PARAM=str(cfile),
                     BUILD_OBJ_OUTPUT_FILENAME_PARAM=str(obj),
                     BUILD_OBJ_CC_OPTIONS_PARAM="-D___DYNAMIC" + (" -O3" if args.syntax_runtime else "")
                     + (" -g" if args.original_std_debug_options and module_path.startswith('std/') else ""),
                     BUILD_OBJ_META_INFO_FILE_PARAM=str(cfile))
            prior = verified_prior or reusable.get(str(native.relative_to(home)))
            prior_root = verified_root if verified_prior else reuse_root
            reused = False
            if prior:
                prior_c = prior_root / 'units' / str(prior['index']) / 'module.c'
                prior_obj = prior_root / prior['object']
                if (hashlib.sha256(native.read_bytes()).hexdigest() != prior['originalSha256']
                        or hashlib.sha256(scm.read_bytes()).hexdigest() != prior['sourceSha256']):
                    raise RuntimeError('qualified Native source inputs changed')
                if cfile.read_bytes() == prior_c.read_bytes():
                    prior_digest = hashlib.sha256(prior_obj.read_bytes()).hexdigest()
                    if prior.get('objectSha256', prior_digest) != prior_digest:
                        raise RuntimeError('qualified Native object hash changed')
                    shutil.copyfile(prior_obj, obj)
                    if hashlib.sha256(obj.read_bytes()).hexdigest() != prior_digest:
                        raise RuntimeError('Native object copy changed bytes')
                    reused = True
                elif not args.gambit_macro_inputs:
                    raise RuntimeError('qualified Native regenerated C changed without macro recipe correction')
            if not reused:
                elapsed += invoke(f"compile-{index}", [str(script), "obj"], process_env=e)
            parity = {}
            if args.verify_installed_native_text:
                linked = folder/'original-recipe.o1'
                link_env = dict(env, GAMBITDIR_INCLUDE=str(home/'include'),
                    GAMBITDIR_LIB=str(home/'lib'), BUILD_DYN_INPUT_FILENAMES_PARAM=str(obj),
                    BUILD_DYN_META_INFO_FILE_PARAM=str(cfile), BUILD_DYN_OUTPUT_FILENAME_PARAM=str(linked),
                    BUILD_DYN_LD_OPTIONS_PARAM=' '.join(
                        f'-Wl,-needed_library,{path}' for path in dependency_inventory[str(native)]
                        if path != '/usr/lib/libSystem.B.dylib'))
                elapsed += invoke(f"parity-link-{index}", [str(script), 'dyn'], process_env=link_env)
                original_text, rebuilt_text = [text_section(path.read_bytes()) for path in (native, linked)]
                if original_text != rebuilt_text:
                    raise RuntimeError(f'{module_path}: installed native text differs from original-recipe object')
                parity = dict(installedNativeTextByteExact=True,
                              installedNativeTextSha256=hashlib.sha256(original_text).hexdigest())
            return {"module": mod, "path": str(native.relative_to(home)), "index": index, **parity,
                    "originalSha256": hashlib.sha256(native.read_bytes()).hexdigest(),
                    "sourceSha256": hashlib.sha256(scm.read_bytes()).hexdigest(),
                    "generatedCSha256": hashlib.sha256(cfile.read_bytes()).hexdigest(),
                    "objectSha256": hashlib.sha256(obj.read_bytes()).hexdigest(),
                    "reusedQualifiedObject": reused,
                    "dependencies": dependency_inventory[str(native)],
                    "object": str(obj.relative_to(output)), "linkerBasename": native.name,
                    "wallSeconds": elapsed}

        print(f"STARTUP-IMAGE native closure {len(images)} files; {cores} GNU workers", flush=True)
        with ThreadPoolExecutor(max_workers=cores) as pool:
            futures = [pool.submit(compile_unit, index, item) for index, item in enumerate(images)]
            try:
                for future in as_completed(futures):
                    report["units"].append(future.result())
                    save()
                    print(f"UNIT-OK {len(report['units'])}/{len(images)}", flush=True)
            except BaseException as error:
                report['failure'] = repr(error)
                save()
                print(f'UNIT-FAIL {error}', flush=True)
                for future in futures:
                    future.cancel()
                raise
        if args.verify_installed_native_text:
            report['installedNativeTextParityProven'] = all(
                row.get('installedNativeTextByteExact') is True for row in report['units'])
        if args.syntax_runtime:
            for row in report["units"]:
                target = candidate / "build" / row["path"]
                target.parent.mkdir(parents=True, exist_ok=True)
                e = dict(env)
                e.update(GAMBITDIR_INCLUDE=str(home / "include"), GAMBITDIR_LIB=str(home / "lib"),
                         BUILD_DYN_INPUT_FILENAMES_PARAM=str(output / row["object"]),
                         BUILD_DYN_OUTPUT_FILENAME_PARAM=str(target),
                         BUILD_DYN_META_INFO_FILE_PARAM=str(work / str(row["index"]) / "module.c"))
                invoke(f"syntax-link-{row['index']}", [str(script), "dyn"], process_env=e)
            overlay = candidate / "build/lib"
            e = dict(env)
            e["GERBIL_LOADPATH"] = f"{overlay}:{home / 'lib'}"
            invoke("candidate-import", [str(home / "bin/gxi"), "-e",
                   '(import :std/make :std/test :std/build-script) (displayln "IMPORT-OK")'], process_env=e)
            if not (output / "candidate-import.log").read_text().rstrip().endswith("IMPORT-OK"):
                raise RuntimeError("syntax runtime overlay failed import smoke")
            report["libraryOverlay"] = str(overlay.relative_to(repo))
            report["imageCountUnchanged"] = True
            report["binaryHashesUnchanged"] = True
            report["qualified"] = True
            return
        groups = []
        for row in sorted(report["units"], key=lambda r: r["index"]):
            group = next((g for g in groups if all(r["linkerBasename"] != row["linkerBasename"] for r in g)), None)
            if group is None:
                group = []
                groups.append(group)
            group.append(row)
        aggregate = candidate / "build/lib/startup-images"
        aggregate.mkdir()
        report['images'] = []
        for index, group in enumerate(groups):
            image = aggregate / f"group-{index}.o1"
            e = dict(env)
            required_dependencies = sorted({path for row in group for path in row['dependencies']})
            dependency_options = ' '.join(f'-Wl,-needed_library,{path}' for path in required_dependencies
                                          if path != '/usr/lib/libSystem.B.dylib')
            e.update(GAMBITDIR_INCLUDE=str(home / "include"), GAMBITDIR_LIB=str(home / "lib"),
                     BUILD_DYN_INPUT_FILENAMES_PARAM=" ".join(str(output / r["object"]) for r in group),
                     BUILD_DYN_OUTPUT_FILENAME_PARAM=str(image),
                     BUILD_DYN_LD_OPTIONS_PARAM=f"-Wl,-undefined,dynamic_lookup {dependency_options}")
            invoke(f"link-{index}", [str(script), "dyn"], process_env=e)
            if dependencies(image.read_bytes()) != required_dependencies:
                raise RuntimeError('packed image changed original strong dependency set')
            # The prototype aliases only immutable toolchain images, never project outputs.
            for row in group:
                target = candidate / "build" / row["path"]
                target.unlink()
                target.symlink_to(os.path.relpath(image, target.parent))
            report['images'].append(dict(path=str(image.relative_to(candidate / 'build')),
                                        sha256=hashlib.sha256(image.read_bytes()).hexdigest(),
                                        aliases=[row['path'] for row in group], dependencies=required_dependencies))
            print(f"IMAGE-OK {index}: {len(group)} original entry points", flush=True)
        report["originalImageCount"] = len(images)
        report["aggregateImageCount"] = len(groups)
        report["candidate"] = str(candidate.relative_to(repo))
        report["binaryHashesUnchanged"] = all(
            hashlib.sha256((home / "bin" / name).read_bytes()).digest()
            == hashlib.sha256((candidate / "build/bin" / name).read_bytes()).digest()
            for name in ("gxi", "gsc"))
        e = dict(env)
        h = candidate / "build"
        e.update(GERBIL_HOME=str(h), GERBIL_LOADPATH=str(h / "lib"),
                 GAMBOPT=f"~~bin={h / 'bin'},~~lib={h / 'lib'},~~include={h / 'include'}",
                 PATH=f"{h / 'bin'}:{env['PATH']}")
        if project:
            e.update(GERBIL_LOADPATH=f"{project / '.gerbil/lib'}:{h / 'lib'}:{project}")
            e['GAMBOPT'] += ',max-heap=1G,debug=q'
        invoke("candidate-import", [str(h / "bin/gxi"), "-e",
               (native_admission_expression(project).replace('(let ((stats',
                '(import :gerbil/tools/gxpkg :std/make :std/build-script) (let ((stats', 1)
                if args.official_tools else native_admission_expression(project)) if project else
               '(import :std/make :std/test :std/build-script) (displayln "IMPORT-OK")'], process_env=e)
        content = (output / "candidate-import.log").read_text()
        marker = 'NATIVE-ADMISSION-PREFIX-OK' if project else 'IMPORT-OK'
        if marker+'\n' not in content or '*** ERROR' in content:
            raise RuntimeError("aggregated closure failed its import marker")
        if args.gambit_macro_inputs and '*** WARNING -- Variable "macro-' in content:
            raise RuntimeError('corrected startup images still contain undefined macro references')
        report["qualified"] = True
    except BaseException as error:
        report["failure"] = str(error)
        raise
    finally:
        report["hostLoadEnd"] = os.getloadavg()
        save()


if __name__ == "__main__":
    main()
