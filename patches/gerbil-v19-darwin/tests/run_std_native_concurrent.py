"""Unmodified staging std/test owners through the original CI Native harness."""
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
from build_runtime_image_composition import SCOPE as COMPOSITION_SCOPE, validate_composed_runtime
from macho_image_dependencies import validate_packed_image_inventory
from run_parser_native_admission_cost import run


OWNERS = (
    'assert-test.ss', 'values-test.ss', 'instance-test.ss', 'misc/ports-test.ss',
    'number/writer-test.ss', 'string/path-test.ss', 'text/markup/html-test.ss',
    'text/markup/sxml-test.ss', 'number/misc-test.ss', 'iter/iter-test.ss',
    'struct/queue-test.ss',
)
FFI_OWNERS = ('crypto/digest-test.ss', 'crypto/cipher-test.ss', 'crypto/pkey-test.ss',
              'net/ssl/socket-test.ss')
HARNESS = 't/fixtures/tla-sany-differential/native-suite.ss'


def batch_cases(content):
    lines = content.splitlines()
    cases = [line for line in lines if line.startswith('CASE-OK ')]
    if (not cases or 'HARNESS-RETURN status=0' not in lines or 'FINAL-GC-OK' not in lines
            or 'NATIVE-SUITE-OK modules=1' not in lines or not lines or lines[-1] != 'OK'
            or any('*** ERROR' in line or line.startswith('ERROR ') for line in lines)):
        raise RuntimeError('standard Native owner failed unchanged case/exit/GC/final-OK gates')
    return cases


def admitted_owners(previous, head, project_head, hashes):
    if (previous.get('qualified') is not False or previous.get('stagingHead') != head
            or previous.get('projectHead') != project_head or previous.get('sourceSha256') != hashes
            or previous.get('wallBudgetSeconds') != 90 or previous.get('silenceBudgetSeconds') != 5
            or len(previous.get('waves', [])) != 1):
        raise RuntimeError('exact original baseline admission failure required')
    wave = previous['waves'][0]
    if (wave.get('role') != 'baseline' or len(wave.get('failures', [])) != 1
            or wave['failures'][0]['owner'] != 'string/path-test.ss'
            or {row['owner'] for row in wave.get('runs', [])} != set(OWNERS)-{'string/path-test.ss'}):
        raise RuntimeError('only recorded Darwin baseline path owner can be excluded from speed subset')
    return tuple(owner for owner in OWNERS if owner != 'string/path-test.ss')


def main():
    parser = argparse.ArgumentParser()
    for name in ('baseline', 'candidate', 'build-receipt', 'project', 'output'):
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--baseline-admission-receipt', type=Path)
    parser.add_argument('--capture-phases', action='store_true')
    parser.add_argument('--ffi-admission', action='store_true')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    baseline, candidate, receipt, project, output = (path.resolve() for path in
        (args.baseline, args.candidate, args.build_receipt, args.project, args.output))
    if not all(path.is_relative_to(root/'.data') for path in (baseline, candidate, receipt, project, output)):
        parser.error('durable isolated .data inputs required')
    build = json.loads(receipt.read_text())
    if args.ffi_admission and args.baseline_admission_receipt:
        parser.error('FFI admission does not exclude any original owner')
    if build.get('scope') == COMPOSITION_SCOPE:
        validate_composed_runtime(candidate/'build', build, baseline/'build')
    else:
        if (not args.ffi_admission or build.get('scope') != 'current-staging-native-preload-image-packing-prototype'
                or build.get('qualified') is not True or build.get('binaryHashesUnchanged') is not True
                or build.get('originalGambitMacroInputsUsed') is not True
                or build.get('consumerFlagsChanged') is not False or build.get('runtimeAbiChanged') is not False):
            parser.error('qualified unchanged-runtime image candidate required for FFI admission')
        validate_packed_image_inventory(candidate/'build', build)
        for source in (baseline, candidate):
            if hashlib.sha256((source/'build/include/gambit.h').read_bytes()).hexdigest() != build['headerSha256']:
                parser.error('image-only FFI header identity changed')
        for name in ('gxi', 'gsc'):
            if (hashlib.sha256((baseline/'build/bin'/name).read_bytes()).digest()
                    != hashlib.sha256((candidate/'build/bin'/name).read_bytes()).digest()):
                parser.error('image-only FFI candidate changed runtime or compiler')
        for row in [*build['units'], *build.get('preservedOriginalImages', [])]:
            original = baseline/'build'/row['path']
            proposed = candidate/'build'/row['path']
            if (hashlib.sha256(original.read_bytes()).hexdigest() != row['originalSha256']
                    or hashlib.sha256(original.with_suffix('.scm').read_bytes()).hexdigest() != row['sourceSha256']
                    or hashlib.sha256(proposed.with_suffix('.scm').read_bytes()).hexdigest() != row['sourceSha256']):
                parser.error('FFI candidate image or Scheme source identity changed')
    head = subprocess.check_output(['git', '-C', str(baseline), 'rev-parse', 'HEAD'], text=True).strip()
    project_head = subprocess.check_output(['git', '-C', str(project), 'rev-parse', 'HEAD'], text=True).strip()
    if project_head != build['projectHead']:
        parser.error('original CI harness head changed')
    sources = [(project, name) for name in (HARNESS,
        't/fixtures/tla-sany-differential/preload.ss',
        't/fixtures/tla-sany-differential/exit-child-process.ss')]
    owners = FFI_OWNERS if args.ffi_admission else OWNERS
    sources += [(baseline, 'src/std/'+name) for name in owners]
    hashes = {}
    for checkout, name in sources:
        selected_head = head if checkout == baseline else project_head
        data = (checkout/name).read_bytes()
        if data != subprocess.check_output(['git', '-C', str(checkout), 'show', f'{selected_head}:{name}']):
            parser.error('original standard test or CI harness source changed')
        hashes[name] = hashlib.sha256(data).hexdigest()
    admission = None
    if args.baseline_admission_receipt:
        admission = args.baseline_admission_receipt.resolve()
        if not admission.is_relative_to(root/'.data'):
            parser.error('isolated baseline failure receipt required')
        owners = admitted_owners(json.loads(admission.read_text()), head, project_head, hashes)
    environment = build_environment()
    cores = int(subprocess.check_output(['sysctl', '-n', 'hw.physicalcpu'], text=True))
    replicas = max(1, cores//len(owners)) if args.ffi_admission else 1
    jobs = owners*replicas
    output.mkdir(parents=True, exist_ok=False)
    report = dict(qualified=False, performanceQualified=False,
                  scope=f'{len(owners)}-original-{"ffi" if args.ffi_admission else "standard"}-test-owners-concurrent-abba-not-full-suite',
                  stagingHead=head, projectHead=project_head, workers=cores, sourceSha256=hashes,
                  buildReceiptSha256=hashlib.sha256(receipt.read_bytes()).hexdigest(),
                  wallBudgetSeconds=90, silenceBudgetSeconds=5, waves=[])
    report['capturePhases'] = args.capture_phases
    report.update(replicasPerOwner=replicas, jobsPerWave=len(jobs), ffiAdmission=args.ffi_admission)
    if admission:
        report.update(baselineAdmissionReceiptSha256=hashlib.sha256(admission.read_bytes()).hexdigest(),
                      excludedBaselineOwner='string/path-test.ss', fullSuiteQualified=False)
    try:
        for wave, role in enumerate(('baseline', 'candidate', 'candidate', 'baseline')):
            home = (baseline if role == 'baseline' else candidate)/'build'
            env = dict(environment)
            for key in list(env):
                if key.startswith('GAMBIT_DARWIN_'):
                    env.pop(key)
            env.update(GERBIL_HOME=str(home), GERBIL_GSC=str(home/'bin/gsc'),
                       GERBIL_BUILD_CORES=str(cores), GERBIL_PATH=str(project/'.gerbil'),
                       GERBIL_LOADPATH=f"{project/'.gerbil/lib'}:{home/'lib'}:{project}",
                       PATH=f"{home/'bin'}:{environment['PATH']}", GERBIL_PARSER_LR_TRACE='1',
                       GAMBOPT=f"~~bin={home/'bin'},~~lib={home/'lib'},~~include={home/'include'},max-heap=1G,debug=q")
            def execute(index, owner):
                log = output/f'{wave}-{role}-{index}.log'
                result = run([str(home/'bin/gxi'), HARNESS, str(baseline/'src/std'/owner)],
                             project, env, log, 90, 5, capture_phases=args.capture_phases)
                result.update(owner=owner, cases=batch_cases(log.read_text()))
                return result
            before = resource.getrusage(resource.RUSAGE_CHILDREN)
            started = time.monotonic()
            wave_report = dict(role=role, index=wave, runs=[], failures=[])
            report['waves'].append(wave_report)
            with ThreadPoolExecutor(max_workers=cores) as pool:
                futures = [(owner, pool.submit(execute, index, owner)) for index, owner in enumerate(jobs)]
                for owner, future in futures:
                    try:
                        wave_report['runs'].append(future.result())
                    except BaseException as error:
                        wave_report['failures'].append(dict(owner=owner, failure=repr(error)))
            after = resource.getrusage(resource.RUSAGE_CHILDREN)
            wave_report.update(wallSeconds=time.monotonic()-started,
                               userCpuSeconds=after.ru_utime-before.ru_utime,
                               systemCpuSeconds=after.ru_stime-before.ru_stime, hostLoad=os.getloadavg())
            state = 'FAILED' if wave_report['failures'] else 'OK'
            print(f'STD-NATIVE-WAVE-{state} role={role} owners={len(owners)}', flush=True)
        report['candidateAllPassed'] = all(not wave['failures'] for wave in report['waves']
                                            if wave['role'] == 'candidate')
        report['baselineAllPassed'] = all(not wave['failures'] for wave in report['waves']
                                           if wave['role'] == 'baseline')
        expected = {}
        for wave in report['waves']:
            for row in wave['runs']:
                if row['owner'] in expected and row['cases'] != expected[row['owner']]:
                    raise RuntimeError('actual standard case identities differ across ABBA waves')
                expected[row['owner']] = row['cases']
        report['completedCaseIdentitiesMatch'] = True
        if not report['candidateAllPassed'] or not report['baselineAllPassed']:
            raise RuntimeError('standard concurrent ABBA failed unchanged Native gates; all waves retained')
        if set(expected) != set(owners):
            raise RuntimeError('actual standard case identities differ across ABBA waves')
        report['qualified'] = True
    except BaseException as error:
        report['failure'] = repr(error)
        raise
    finally:
        (output/'report.json').write_text(json.dumps(report, indent=2)+'\n')


if __name__ == '__main__':
    main()
