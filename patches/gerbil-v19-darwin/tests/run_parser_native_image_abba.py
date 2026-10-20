"""Real unchanged parser Native batch; image-packing candidate remains experimental."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import resource
import subprocess
import time

from bazel_host_environment import build_environment
from run_parser_native_admission_cost import run
from macho_image_dependencies import validate_packed_image_inventory
from build_runtime_image_composition import SCOPE as COMPOSITION_SCOPE, validate_composed_runtime


def validate_batch(content):
    lines = content.splitlines()
    cases = sum(line.startswith('CASE-OK ') for line in lines)
    if (cases != 5 or 'HARNESS-RETURN status=0' not in lines or 'FINAL-GC-OK' not in lines
            or 'NATIVE-SUITE-OK modules=1' not in lines or not lines or lines[-1] != 'OK'
            or any('*** ERROR' in line or line.startswith('ERROR ') for line in lines)):
        raise RuntimeError('real five-case Native batch failed its unchanged exit/GC/final-OK contract')
    return cases


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--build-receipt', type=Path, required=True)
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--concurrent-candidate', action='store_true')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    baseline, candidate, receipt, project, output = (path.resolve() for path in
        (args.baseline, args.candidate, args.build_receipt, args.project, args.output))
    if not all(path.is_relative_to(root / '.data') for path in (baseline, candidate, receipt, project, output)):
        parser.error('isolated .data inputs/output required')
    build = json.loads(receipt.read_text())
    composed = build.get('scope') == COMPOSITION_SCOPE
    if (build.get('qualified') is not True or not composed and build.get('binaryHashesUnchanged') is not True
            or build.get('originalGambitMacroInputsUsed') is not True
            or build.get('scope') not in ('current-staging-native-preload-image-packing-prototype', COMPOSITION_SCOPE)
            or build.get('consumerFlagsChanged') is not False or build.get('runtimeAbiChanged') is not False):
        parser.error('completed current-staging image packing receipt required')
    head = subprocess.check_output(['git', '-C', str(project), 'rev-parse', 'HEAD'], text=True).strip()
    if head != build['projectHead']:
        parser.error('referenced Native project head changed')
    home, chome = baseline / 'build', candidate / 'build'
    validate_packed_image_inventory(chome, build)
    if composed:
        validate_composed_runtime(chome, build, home)
    else:
        for name in ('gxi', 'gsc'):
            if hashlib.sha256((home / 'bin' / name).read_bytes()).digest() != hashlib.sha256((chome / 'bin' / name).read_bytes()).digest():
                parser.error('image candidate changed runtime or compiler')
    for row in build['units']:
        original = home / row['path']
        if (hashlib.sha256(original.read_bytes()).hexdigest() != row['originalSha256']
                or hashlib.sha256(original.with_suffix('.scm').read_bytes()).hexdigest() != row['sourceSha256']
                or hashlib.sha256((chome / row['path']).with_suffix('.scm').read_bytes()).hexdigest() != row['sourceSha256']):
            parser.error('original Native image/Scheme source provenance changed')
    environment = build_environment()
    cores = int(subprocess.check_output(['sysctl', '-n', 'hw.physicalcpu'], text=True))
    output.mkdir(parents=True, exist_ok=False)
    files = ('t/fixtures/tla-sany-differential/native-suite.ss',
             't/fixtures/tla-sany-differential/preload.ss', 't/test-style-contract-test.ss')
    hashes = {}
    for name in files:
        data = (project / name).read_bytes()
        if data != subprocess.check_output(['git', '-C', str(project), 'show', f'{head}:{name}']):
            parser.error('original CI Native test source changed')
        hashes[name] = hashlib.sha256(data).hexdigest()
    report = dict(qualified=False, performanceQualified=False,
                  scope=('real-native-one-owner-image-hardware-concurrent-not-full-suite' if args.concurrent_candidate
                         else 'real-native-one-owner-image-abba-not-full-suite'),
                  projectHead=head, cores=cores, runs=[], sourceSha256=hashes,
                  buildReceiptSha256=hashlib.sha256(receipt.read_bytes()).hexdigest(),
                  runtimeSha256=hashlib.sha256((home / 'bin/gxi').read_bytes()).hexdigest(),
                  packedImageHashesLocked=True,
                  composedRuntime=composed,
                  candidateRuntimeSha256=hashlib.sha256((chome / 'bin/gxi').read_bytes()).hexdigest(),
                  wallBudgetSeconds=90, silenceBudgetSeconds=5)
    try:
        def execute(index, role):
            selected = home if role == 'baseline' else chome
            env = dict(environment)
            for key in list(env):
                if key.startswith('GAMBIT_DARWIN_'):
                    env.pop(key)
            env.update(GERBIL_HOME=str(selected), GERBIL_GSC=str(selected / 'bin/gsc'),
                       GERBIL_PATH=str(project / '.gerbil'),
                       GERBIL_LOADPATH=f"{project / '.gerbil/lib'}:{selected / 'lib'}:{project}",
                       PATH=f"{selected / 'bin'}:{environment['PATH']}", GERBIL_BUILD_CORES=str(cores),
                       GERBIL_PARSER_LR_TRACE='1',
                       GAMBOPT=f"~~bin={selected / 'bin'},~~lib={selected / 'lib'},~~include={selected / 'include'},max-heap=1G,debug=q")
            before = resource.getrusage(resource.RUSAGE_CHILDREN)
            result = run([str(selected / 'bin/gxi'), files[0], files[2]], project, env,
                         output / f'{index}-{role}.log', 90, 5)
            after = resource.getrusage(resource.RUSAGE_CHILDREN)
            result.update(role=role, index=index, hostLoad=os.getloadavg())
            if not args.concurrent_candidate:
                result.update(userCpuSeconds=after.ru_utime-before.ru_utime,
                              systemCpuSeconds=after.ru_stime-before.ru_stime)
            result['cases'] = validate_batch((output / f'{index}-{role}.log').read_text())
            print(f'NATIVE-BATCH-OK {role} index={index} cases={result["cases"]}', flush=True)
            return result
        if args.concurrent_candidate:
            started = time.monotonic()
            before = resource.getrusage(resource.RUSAGE_CHILDREN)
            with ThreadPoolExecutor(max_workers=cores) as pool:
                futures = [pool.submit(execute, index, 'candidate') for index in range(cores)]
                failures = []
                for future in futures:
                    try:
                        report['runs'].append(future.result())
                    except BaseException as error:
                        failures.append(repr(error))
            after = resource.getrusage(resource.RUSAGE_CHILDREN)
            report.update(batchWallSeconds=time.monotonic()-started,
                          totalUserCpuSeconds=after.ru_utime-before.ru_utime,
                          totalSystemCpuSeconds=after.ru_stime-before.ru_stime)
            if failures:
                report['failures'] = failures
                raise RuntimeError('hardware concurrent Native batch failed unchanged gates')
        else:
            for index, role in enumerate(('baseline', 'candidate', 'candidate', 'baseline')):
                report['runs'].append(execute(index, role))
        report['qualified'] = True
    except BaseException as error:
        report['failure'] = repr(error)
        raise
    finally:
        (output / 'report.json').write_text(json.dumps(report, indent=2)+'\n')


if __name__ == '__main__':
    main()
