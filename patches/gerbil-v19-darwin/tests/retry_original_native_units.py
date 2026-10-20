"""Retry retained original-recipe C units; never admit a full image candidate."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time

from bazel_host_environment import build_environment
from native_object_manifest import digest, text_section
from macho_image_dependencies import dependencies


def construction_budget(receipt):
    if (receipt.get('qualified') is not True
            or receipt.get('consumerFlagsChanged') is not False
            or receipt.get('runtimeAbiChanged') is not False
            or receipt.get('runtimeOptimization') != 'O1'
            or receipt.get('compileWallBudgetSeconds') != 900):
        raise ValueError('successful original-O1 900-second build-only receipt required')
    return 900


def main():
    parser = argparse.ArgumentParser()
    for name in ('baseline', 'retained', 'inventory', 'output'):
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--index', type=int, action='append', required=True)
    parser.add_argument('--construction-budget-receipt', type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    if not all(path.resolve().is_relative_to(root/'.data') for path in
               (args.baseline, args.retained, args.inventory, args.output)):
        parser.error('project-data inputs and fresh output required')
    args.output.mkdir(parents=True, exist_ok=False)
    home = args.baseline.resolve()/'build'
    prior = json.loads((args.retained/'report.json').read_text())
    if (prior.get('originalStdDebugOptionsUsed') is not True
            or prior.get('originalGambitMacroInputsUsed') is not True
            or digest(home/'bin/gsc') != prior['gscSha256']
            or digest(home/'include/gambit.h') != prior['headerSha256']
            or digest(home/'lib/_gambit#.scm') != prior['macroInputSha256']):
        raise ValueError('current original-debug retained compiler inputs required')
    inventory = json.loads(args.inventory.read_text())
    selected = [row for row in inventory['units'] if row['index'] in args.index]
    if len(selected) != len(set(args.index)):
        raise ValueError('exact original unit indices required')
    env = build_environment()
    macros = subprocess.check_output([env['CC'], '-dM', '-E', '-x', 'c', os.devnull], env=env, text=True)
    if '#define __clang__' in macros or '#define __APPLE__' not in macros or '#define __GNUC__ 16\n' not in macros:
        raise ValueError('Darwin real GNU GCC 16 required')
    workers = int(subprocess.check_output(['sysctl', '-n', 'hw.physicalcpu'], text=True))
    report = dict(scope='retained-original-native-unit-retry-not-full-image-admission',
                  qualified=False, performanceQualified=False, hardwareWorkers=workers,
                  taskCount=len(selected), nativeInvocationBudgetSeconds=180,
                  retainedReceiptSha256=digest(args.retained/'report.json'), runs=[])
    if args.construction_budget_receipt:
        receipt_path = args.construction_budget_receipt.resolve()
        if not receipt_path.is_relative_to(root/'.data'):
            parser.error('isolated successful construction receipt required')
        budget_receipt = json.loads(receipt_path.read_text())
        report.update(nativeInvocationBudgetSeconds=construction_budget(budget_receipt),
                      constructionBudgetReceiptSha256=digest(receipt_path),
                      productOutputBudgetsChanged=False)

    def retry(row):
        original = home/row['path']
        cfile = args.retained/'units'/str(row['index'])/'module.c'
        hashes = dict(original=digest(original), source=digest(original.with_suffix('.scm')), c=digest(cfile))
        if hashes['original'] != row['originalSha256'] or hashes['source'] != row['sourceSha256']:
            raise ValueError('original installed inputs changed')
        directory = args.output/str(row['index'])
        directory.mkdir()
        obj, image = directory/'module.o', directory/'module.o1'
        native_env = dict(env, GAMBITDIR_INCLUDE=str(home/'include'), GAMBITDIR_LIB=str(home/'lib'),
            BUILD_OBJ_INPUT_FILENAMES_PARAM=str(cfile.resolve()), BUILD_OBJ_OUTPUT_FILENAME_PARAM=str(obj.resolve()),
            BUILD_OBJ_META_INFO_FILE_PARAM=str(cfile.resolve()), BUILD_OBJ_CC_OPTIONS_PARAM='-D___DYNAMIC -g',
            BUILD_DYN_INPUT_FILENAMES_PARAM=str(obj.resolve()), BUILD_DYN_OUTPUT_FILENAME_PARAM=str(image.resolve()),
            BUILD_DYN_META_INFO_FILE_PARAM=str(cfile.resolve()), GAMBUILD_VERBOSE='1',
            BUILD_DYN_LD_OPTIONS_PARAM=' '.join('-Wl,-needed_library,'+path for path in dependencies(original.read_bytes())
                                             if path != '/usr/lib/libSystem.B.dylib'))
        result = dict(index=row['index'], module=row['module'], generatedCSha256=hashes['c'], passed=False)
        try:
            for mode in ('obj', 'dyn'):
                print(f"NATIVE-{mode.upper()}-START {row['module']}", flush=True)
                started = time.monotonic()
                with (directory/(mode+'.log')).open('w') as log:
                    process = subprocess.Popen([str(home/'bin/gambuild-C'), mode], env=native_env,
                        stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
                    try:
                        status = process.wait(timeout=report['nativeInvocationBudgetSeconds'])
                    finally:
                        if process.poll() is None:
                            os.killpg(process.pid, signal.SIGTERM)
                            try:
                                process.wait(timeout=5)
                            except subprocess.TimeoutExpired:
                                os.killpg(process.pid, signal.SIGKILL)
                                process.wait(timeout=5)
                result[mode+'WallSeconds'] = time.monotonic()-started
                if status:
                    raise RuntimeError(f'{mode} exit {status}')
            texts = [text_section(path.read_bytes()) for path in (original, image)]
            if digest(cfile) != hashes['c'] or digest(original) != hashes['original']:
                raise ValueError('retained inputs changed during native compilation')
            result.update(nativeTextByteExact=texts[0] == texts[1],
                          nativeTextSha256=[hashlib.sha256(text).hexdigest() for text in texts],
                          objectSha256=digest(obj), passed=texts[0] == texts[1])
        except BaseException as error:
            result['failure'] = repr(error)
        print(f"NATIVE-RETRY-END {row['module']} passed={result['passed']}", flush=True)
        return result

    try:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            report['runs'] = list(pool.map(retry, selected))
        report['allSelectedUnitsPassed'] = all(row['passed'] for row in report['runs'])
    finally:
        (args.output/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    if not report.get('allSelectedUnitsPassed'):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
