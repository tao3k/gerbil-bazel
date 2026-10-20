"""Capture ordinary installed toolchain objects missing from the retained provider.

Construction evidence only; module selection is a pilot, not release coverage.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import subprocess

from audit_startup_gsc_recipe import gsc_recipe_command
from bazel_host_environment import build_environment
from macho_image_dependencies import dependencies
from native_object_manifest import digest, text_section
from run_parser_native_admission_cost import run


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--module', action='append', required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    output = args.output.resolve()
    if output.exists() or not output.is_relative_to(root / '.data'):
        parser.error('fresh persistent .data output required')
    home = root / '.data/d1391-runtime-object-source/build'
    inventory_path = root / '.data/d1543-current-active-native-images/report.json'
    provider_path = root / '.data/d1510-reader-whitespace-native-v2/report.json'
    inventory = json.loads(inventory_path.read_text())
    provider = json.loads(provider_path.read_text())
    if not inventory['qualified'] or not provider['qualified']:
        raise ValueError('qualified original inventory and retained provider required')
    selected = [row for row in inventory['units'] if row['module'] in args.module]
    if (len(selected) != len(set(args.module)) or len(args.module) != len(set(args.module))
            or any(not row['ordinarySystemImage'] for row in selected)
            or any(row['module'] in {p['module'] for p in provider['providers']} for row in selected)):
        raise ValueError('distinct uncovered ordinary toolchain modules required')
    inputs = {'bin/gerbil': inventory['binarySha256'], 'bin/gsc': inventory['gscSha256'],
              'include/gambit.h': inventory['headerSha256'],
              'lib/_gambit#.scm': inventory['macroInputSha256'],
              'lib/libgambit.a': inventory['runtimeArchiveSha256']}
    for row in selected:
        inputs[row['path']] = row['originalSha256']
        inputs[str(Path(row['path']).with_suffix('.scm'))] = row['sourceSha256']
    if any(digest(home / path) != expected for path, expected in inputs.items()):
        raise ValueError('original toolchain input identity changed')
    env = build_environment()
    macros = subprocess.check_output([env['CC'], '-dM', '-E', '-x', 'c', os.devnull], env=env, text=True)
    if '#define __GNUC__ 16\n' not in macros or '#define __APPLE__' not in macros or '#define __clang__' in macros:
        raise ValueError('retained Darwin GNU GCC 16 required')
    cores = int(subprocess.check_output(['sysctl', '-n', 'hw.physicalcpu'], text=True))
    env.update(GERBIL_HOME=str(home), GERBIL_BUILD_CORES=str(cores),
               GAMBOPT=f'~~bin={home / "bin"},~~lib={home / "lib"},~~include={home / "include"}')
    output.mkdir()
    report = dict(scope='ordinary-toolchain-provider-extension-object-construction-only',
                  qualified=False, performanceQualified=False, productionAdmitted=False,
                  selectedModules=args.module, consumerPackages=[], hardwareWorkers=cores,
                  inventorySha256=digest(inventory_path), providerReceiptSha256=digest(provider_path),
                  inputHashes=inputs, runs=[])

    def capture(row):
        folder = output / str(row['index'])
        folder.mkdir()
        cfile, obj, image = folder / 'module.c', folder / 'module.o', folder / 'module.o2'
        result = dict(module=row['module'], activePath=row['path'], passed=False, steps=[])
        try:
            command = gsc_recipe_command(home, row['module'], cfile, original_std_debug=True,
                                         native_version=row['activeVersion'])
            result['steps'].append(run(command, folder, env, folder / 'generate.log', 180))
            native = dict(env, GAMBITDIR_INCLUDE=str(home / 'include'), GAMBITDIR_LIB=str(home / 'lib'),
                          BUILD_OBJ_INPUT_FILENAMES_PARAM=str(cfile), BUILD_OBJ_META_INFO_FILE_PARAM=str(cfile),
                          BUILD_OBJ_OUTPUT_FILENAME_PARAM=str(obj),
                          BUILD_OBJ_CC_OPTIONS_PARAM='-D___DYNAMIC' + (' -g' if row['module'].startswith('std/') else ''),
                          BUILD_DYN_INPUT_FILENAMES_PARAM=str(obj), BUILD_DYN_META_INFO_FILE_PARAM=str(cfile),
                          BUILD_DYN_OUTPUT_FILENAME_PARAM=str(image),
                          BUILD_DYN_LD_OPTIONS_PARAM=' '.join('-Wl,-needed_library,' + dep for dep in row['dependencies']
                                                             if dep != '/usr/lib/libSystem.B.dylib'))
            for mode in ('obj', 'dyn'):
                result['steps'].append(run([str(home / 'bin/gambuild-C'), mode], folder, native,
                                          folder / (mode + '.log'), 180))
            result.update(nativeTextByteExact=text_section((home / row['path']).read_bytes()) == text_section(image.read_bytes()),
                          dependenciesMatch=dependencies(image.read_bytes()) == row['dependencies'],
                          originalUnchanged=all(digest(home / path) == expected for path, expected in inputs.items()),
                          generatedCSha256=digest(cfile), objectSha256=digest(obj), imageSha256=digest(image))
            result['passed'] = all(result[key] for key in ('nativeTextByteExact', 'dependenciesMatch', 'originalUnchanged'))
        except Exception as error:
            result['failure'] = repr(error)
        (folder / 'report.json').write_text(json.dumps(result, indent=2) + '\n')
        print(json.dumps(result), flush=True)
        return result

    try:
        with ThreadPoolExecutor(max_workers=cores) as pool:
            report['runs'] = list(pool.map(capture, selected))
        report['inputsUnchanged'] = all(digest(home / path) == expected for path, expected in inputs.items())
        report['qualified'] = report['inputsUnchanged'] and all(row['passed'] for row in report['runs'])
    finally:
        (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    return 0 if report['qualified'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
