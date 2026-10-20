"""Observe an unchanged parser CI Native preload prefix, never qualify speed."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import selectors
import signal
import subprocess
import time

from bazel_host_environment import build_environment
from run_gambit_startup_cpu import parse_process_statistics


def native_admission_prefix(project):
    return (f'(current-directory {json.dumps(str(project))}) '
            '(load "t/fixtures/tla-sany-differential/preload.ss") '
            '(prefer-native-interfaces!) '
            '(preload-module "gerbil/tools/gxtest") '
            '(preload-module "gerbil-parser/t/fixtures/tla-sany-differential/exit-child-process") '
            '(preload-test-imports "t/test-style-contract-test.ss") ')


def native_admission_expression(project):
    return (native_admission_prefix(project)
            + '(let ((stats (##process-statistics))) '
            '(display "GAMBIT-PROCESS-STATISTICS ") (write (f64vector->list stats)) '
            '(newline) (force-output)) '
            '(displayln "NATIVE-ADMISSION-PREFIX-OK") (force-output) '
            '(import :gerbil-parser/t/fixtures/tla-sany-differential/exit-child-process) '
            '(test-child-process-exit! 0)')


def run(command, project, environment, log_path, wall_budget, idle_budget=None, capture_phases=False,
        on_start=None):
    started = last_output = time.monotonic()
    first_output = None
    first_case = None
    maximum_gap = 0
    phase_events = []
    child = subprocess.Popen(command, cwd=project, env=environment,
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             start_new_session=True)
    pending = b''
    try:
        if on_start is not None:
            on_start(child.pid)
        with log_path.open('wb') as log, selectors.DefaultSelector() as selector:
            selector.register(child.stdout, selectors.EVENT_READ)
            while selector.get_map():
                now = time.monotonic()
                if now-started > wall_budget or idle_budget is not None and now-last_output > idle_budget:
                    raise RuntimeError(f'{log_path.name} exceeded unchanged wall/silence budget')
                for key, _ in selector.select(0.1):
                    data = os.read(key.fd, 65536)
                    if not data:
                        selector.unregister(key.fileobj)
                        continue
                    log.write(data)
                    log.flush()
                    pending += data
                    while b'\n' in pending:
                        line, pending = pending.split(b'\n', 1)
                        now = time.monotonic()
                        maximum_gap = max(maximum_gap, now-last_output)
                        last_output = now
                        if first_output is None:
                            first_output = now-started
                        if first_case is None and line.startswith(b'CASE-OK '):
                            first_case = now-started
                        if capture_phases and line.startswith((b'MODULE-BATCH-START ', b'MODULE-IMPORTED ',
                                                               b'CASE-OK ', b'HARNESS-RETURN ',
                                                               b'FINAL-GC-OK', b'NATIVE-SUITE-OK')):
                            phase_events.append(dict(elapsedSeconds=now-started,
                                                     line=line.decode(errors='replace')))
                        if line.startswith((b'MODULE-IMPORTED ', b'NATIVE-', b'CASE-OK ',
                                            b'HARNESS-RETURN ', b'FINAL-GC-OK', b'*** ERROR')):
                            print(line.decode(errors='replace'), flush=True)
            code = child.wait(timeout=max(0.001, wall_budget-(time.monotonic()-started)))
        if code:
            raise RuntimeError(f'{log_path.name} exited {code}')
        result = dict(exitCode=code, wallSeconds=time.monotonic()-started,
                    firstOutputSeconds=first_output, firstCaseSeconds=first_case,
                    maximumOutputGapSeconds=maximum_gap)
        if capture_phases:
            result['observedPhaseEvents'] = phase_events
        return result
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
        child.stdout.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--observer', type=Path, required=True)
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    baseline, observer, project, output = (p.resolve() for p in
                                          (args.baseline, args.observer, args.project, args.output))
    if not all(p.is_relative_to(root / '.data') for p in (baseline, observer, project, output)):
        parser.error('isolated .data inputs and output required')
    head = subprocess.check_output(['git', '-C', str(project), 'rev-parse', 'HEAD'], text=True).strip()
    if head != 'f35b14193db7cfc89444b0f9a82b81c3862bc795':
        parser.error('exact referenced CI PR head required')
    environment = build_environment()
    macros = subprocess.check_output([environment['CC'], '-dM', '-E', '-x', 'c', os.devnull],
                                     env=environment, text=True)
    if '#define __clang__' in macros or '#define __GNUC__ 16\n' not in macros:
        parser.error('GNU GCC 16 required')
    cores = int(subprocess.check_output(['sysctl', '-n', 'hw.physicalcpu'], text=True))
    output.mkdir(parents=True, exist_ok=False)
    home = baseline / 'build'
    environment.update(GERBIL_HOME=str(home), GERBIL_GSC=str(home / 'bin/gsc'),
                       GERBIL_PATH=str(project / '.gerbil'), GERBIL_BUILD_CORES=str(cores),
                       GERBIL_LOADPATH=f"{project / '.gerbil/lib'}:{home / 'lib'}:{project}",
                       PATH=f"{home / 'bin'}:{environment['PATH']}",
                       GAMBOPT=f"~~bin={home / 'bin'},~~lib={home / 'lib'},~~include={home / 'include'},max-heap=1G,debug=q",
                       GERBIL_PARSER_LR_TRACE='1')
    for key in list(environment):
        if key.startswith('GAMBIT_DARWIN_'):
            environment.pop(key)
    files = ('t/fixtures/tla-sany-differential/preload.ss',
             't/fixtures/tla-sany-differential/native-suite.ss',
             't/fixtures/tla-sany-differential/exit-child-process.ss',
             't/test-style-contract-test.ss')
    for name in files:
        original = subprocess.check_output(['git', '-C', str(project), 'show', f'{head}:{name}'])
        if original != (project / name).read_bytes():
            parser.error('referenced Native source was modified')
    observer_hash = hashlib.sha256((observer / 'build/bin/gxi').read_bytes()).hexdigest()
    if observer_hash != '36dc048245867eebf7e95f47e210fb91e961ea9bc4227994381b0016062ecac9':
        parser.error('previously qualified passive observer binary required')
    report = dict(qualified=False, performanceQualified=False, diagnosticOnly=True,
                  scope='referenced-native-batch-preload-prefix-not-case-or-full-suite',
                  projectHead=head, cores=cores, wallBudgetSeconds=90, silenceBudgetSeconds=5,
                  sourceSha256={name: hashlib.sha256((project / name).read_bytes()).hexdigest() for name in files},
                  observerBinarySha256=observer_hash, runs=[], hostLoadStart=os.getloadavg())
    report.update(nativeExitPolicy=True, sourceCostCountersTerminal=False,
                  sourceCostCoverageQualified=False)
    try:
        library = project / '.gerbil/lib'
        library.mkdir(parents=True, exist_ok=True)
        report['exitBindingBuild'] = run([str(home / 'bin/gxc'), '-V', '-d', str(library),
            '-ld-options', '-Wl,-undefined,dynamic_lookup', files[2]], project, environment,
            output / 'compile-exit-binding.log', 120)
        stem = library / 'gerbil-parser/t/fixtures/tla-sany-differential/exit-child-process'
        artifacts = [stem.with_suffix('.ssi'), stem.with_suffix('.scm')]
        artifacts.extend(stem.parent.glob(stem.name+'*.o1'))
        if len(artifacts) < 3 or not all(path.is_file() for path in artifacts):
            raise RuntimeError('compiled Native exit binding artifacts missing')
        report['exitBindingArtifacts'] = {str(path.relative_to(project)): hashlib.sha256(path.read_bytes()).hexdigest()
                                         for path in artifacts}
        expression = native_admission_expression(project)
        report['expression'] = expression
        report['baselineBinarySha256'] = hashlib.sha256((home / 'bin/gxi').read_bytes()).hexdigest()
        for name, source in (('baseline', baseline), ('observer', observer)):
            child_env = dict(environment)
            if name == 'observer':
                child_env['GAMBIT_DARWIN_SOURCE_COST_PREFIX'] = str(output / 'source-cost')
            result = run([str(source / 'build/bin/gxi'), '-e', expression], project, child_env,
                         output / f'{name}.log', 90, 5)
            result['name'] = name
            report['runs'].append(result)
            content = (output / f'{name}.log').read_text()
            if 'NATIVE-ADMISSION-PREFIX-OK\n' not in content:
                raise RuntimeError('real preload prefix did not complete')
            result['nativeProcessStatistics'] = parse_process_statistics(content)
        paths = list(output.glob('source-cost.*.json'))
        if len(paths) != 1:
            raise RuntimeError('one periodic passive observer receipt required')
        costs = json.loads(paths[0].read_text())
        report['nativeCosts'] = costs
        if costs['errors'] or costs['openFrames']:
            raise RuntimeError('periodic native observer snapshot was not balanced')
        report['qualified'] = True
        print('NATIVE-ADMISSION-COST-OK diagnostic only', flush=True)
    except Exception as error:
        report['failure'] = repr(error)
        raise
    finally:
        report['hostLoadEnd'] = os.getloadavg()
        (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    main()
