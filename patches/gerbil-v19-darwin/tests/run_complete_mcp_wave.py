"""Whole-task 5s/112s acceptance; no extra per-file silence budget."""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import selectors
import shutil
import signal
import subprocess
import time

from bazel_host_environment import build_environment
from mcp_case_inventory import case_names
from selected_gerbil_toolchain import validate_tools
from progressive_performance_gate import GateViolation, Limits, ProgressiveGate, force_stop

TEST_CEILING_SECONDS = 112


def final_test_ok(text):
    statuses = [line for line in text.splitlines()
                if line == 'OK' or line.startswith(
                    ('CASE-FAIL', 'MODULE-FAIL', 'SUITE-FAIL', 'HARNESS-FAIL', '*** ERROR'))]
    return statuses[-1:] == ['OK']


def wave_admission(rows, elapsed):
    failures = []
    correctness = len(rows) == 39 and all(row['passed'] for row in rows)
    duration = type(elapsed) in (int, float) and 0 < elapsed <= TEST_CEILING_SECONDS
    if not correctness:
        failures.append('complete-39-file-correctness-gate-failed')
    if not duration:
        failures.append('complete-test-wave-over-112-second-ceiling-or-invalid-duration')
    return dict(decision='DENY' if failures else 'ALLOW', admitted=not failures,
                failures=failures, ceilingSeconds=TEST_CEILING_SECONDS, targetSeconds=TEST_CEILING_SECONDS,
                targetMet=duration, durationGatePassed=duration, correctnessGatePassed=correctness)


def execution_limits(diagnostic):
    # Completion diagnostics retain a safety bound, never a wider admission gate.
    return Limits('complete-test-wave', complete=900 if diagnostic else TEST_CEILING_SECONDS,
                  first=None if diagnostic else 5, silence=None)


def reap(process):
    errors = []
    for sig in (signal.SIGTERM, signal.SIGKILL):
        if process.poll() is not None:
            break
        try:
            os.killpg(process.pid, sig)
        except ProcessLookupError:
            pass
        except PermissionError as error:
            errors.append(repr(error))
            try:
                process.send_signal(sig)
            except ProcessLookupError:
                pass
            except PermissionError as owned_error:
                errors.append(repr(owned_error))
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            continue
    return dict(errors=errors, reaped=process.poll() is not None,
                terminalExitCode=process.returncode)


def main():
    parser = argparse.ArgumentParser()
    for name in ('binary', 'home', 'project', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--cold-report', type=Path, required=True)
    parser.add_argument('--whole-task-gates', action='store_true')
    parser.add_argument('--integration-first', action='store_true')
    parser.add_argument('--completion-diagnostic', action='store_true')
    args = parser.parse_args()
    if not args.whole_task_gates:
        parser.error('explicit whole-task gate policy selection required')
    root = Path(__file__).resolve().parents[3]
    binary, home, project, out = [getattr(args, key).resolve() for key in
                                  ('binary', 'home', 'project', 'output')]
    if any(not p.is_relative_to(root / '.data') for p in (binary, home, project, out)):
        parser.error('isolated project .data paths required')
    construction = json.loads((binary.parent / 'report.json').read_text())
    expected_sha = construction['binarySha256']
    if not construction['qualified']:
        raise ValueError('construction is not qualified')
    cold_identity = None
    if args.cold_report:
        cold_path = args.cold_report.resolve()
        if not cold_path.is_relative_to(root / '.data'):
            raise ValueError('cold receipt must be isolated')
        cold = json.loads(cold_path.read_text())
        artifact_sha = hashlib.sha256((project / '.gerbil/bin/gerbil-mcp').read_bytes()).hexdigest()
        matching = [row for row in cold['runs'] if row.get('passed') and
                    row.get('sourceUnchanged') and row.get('binarySha256') == expected_sha
                    and row.get('executableSha256') == artifact_sha]
        if not matching:
            raise ValueError('test artifact does not match this candidate cold build')
        cold_identity = dict(reportSha256=hashlib.sha256(cold_path.read_bytes()).hexdigest(),
                             executableSha256=artifact_sha)
    cores = int(subprocess.check_output(['sysctl', '-n', 'hw.physicalcpu'], text=True))
    files = (sorted((project / 'test/unit').glob('*-test.ss')) +
             sorted((project / 'test').glob('chunk-*-test.ss')) +
             [project / 'test/protocol-test.ss'])
    if len(files) != 39 or sum(len(case_names(p)) for p in files) != 965:
        raise ValueError('retained MCP inventory changed')
    if args.integration_first:
        critical = {'chunk-07-test.ss': 0, 'chunk-12-test.ss': 1, 'chunk-18-test.ss': 2}
        files.sort(key=lambda p: (critical.get(p.name, 3 if p.parent.name != 'unit' else 4),
                                  p.name))
    out.mkdir()
    base = build_environment()
    for key in tuple(base):
        if key.startswith('GAMBIT_DARWIN_'):
            base.pop(key)
    base.pop('GERBIL_BUILD_PREFIX', None)
    driver = root / '.data/d1510-shell-substitution/bin'
    base.update(GERBIL_HOME=str(home), GERBIL_PATH=str(project / '.gerbil'),
                GERBIL_LOADPATH=f'{project / ".gerbil/lib"}:{home / "lib"}:{project}',
                GERBIL_GSC=str(driver / 'gsc'), GERBIL_GCC=base['GERBIL_GNU_GCC'],
                GERBIL_BUILD_CORES=str(cores), GAMBIT_EMBEDDED_NATIVE='0',
                GAMBOPT=f'~~bin={driver},~~lib={home / "lib"},~~include={home / "include"}',
                GERBIL_MCP_BIN=str(project / '.gerbil/bin/gerbil-mcp'),
                GERBIL_MCP_MODE='full')

    def run(index_file):
        index, file = index_file
        job = out / str(index)
        job.mkdir()
        entry, tmp = job / 'selected-bin', job / 'tmp'
        entry.mkdir()
        tmp.mkdir()
        env = dict(base, TMPDIR=str(tmp),
                   PATH=f'{entry}:{driver}:{home / "bin"}:{base["PATH"]}')
        for name in ('gerbil', 'gxi', 'gxc', 'gxpkg'):
            (entry / name).symlink_to(binary)
            env['GERBIL_MCP_' + name.upper() + '_PATH'] = str(entry / name)
        relative = str(file.relative_to(project))
        row = dict(testFile=relative, passed=False, attempted=False, binarySha256=expected_sha)
        process = None
        selector = selectors.DefaultSelector()
        started = last = time.monotonic()
        gate = ProgressiveGate(Limits('test-file', complete=900 if args.completion_diagnostic else TEST_CEILING_SECONDS,
                                      first=None, silence=None), started)
        maximum = 0
        before = hashlib.sha256(file.read_bytes()).hexdigest()
        names = case_names(file)
        row['expectedCaseNames'] = names
        try:
            wave_gate.check(time.monotonic())
            validation_started = time.monotonic()
            row['selectedToolchain'] = validate_tools(env, binary, expected_sha)
            row['toolchainValidationSeconds'] = time.monotonic() - validation_started
            gsc = Path(shutil.which('gsc', path=env['PATH'])).resolve(strict=True)
            gsc_sha = hashlib.sha256(gsc.read_bytes()).hexdigest()
            if gsc != (driver / 'gsc').resolve(strict=True) or gsc_sha != construction['gscSha256']:
                raise ValueError('Gambit compiler escapes selected build')
            row['selectedGscSha256'] = gsc_sha
            process = subprocess.Popen([str(binary), 'test', '-v', '5', relative],
                                       cwd=project, env=env, stdout=subprocess.PIPE,
                                       stderr=subprocess.STDOUT, start_new_session=True)
            row['attempted'] = True
            row['spawnElapsedSeconds'] = time.monotonic() - started
            selector.register(process.stdout, selectors.EVENT_READ)
            with (job / 'test.log').open('wb') as log:
                while selector.get_map() or process.poll() is None:
                    now = time.monotonic()
                    if args.completion_diagnostic and now - wave_started > TEST_CEILING_SECONDS:
                        diagnostic_denials.setdefault('completeTest', dict(
                            decision='DENY', ceilingSeconds=TEST_CEILING_SECONDS,
                            observedElapsedSeconds=now - wave_started,
                            executionContinuedForCorrectness=True))
                    wave_gate.check(now)
                    gate.check(now)
                    for key, _ in selector.select(timeout=0.1):
                        chunk = os.read(key.fileobj.fileno(), 65536)
                        if not chunk:
                            selector.unregister(key.fileobj)
                            continue
                        observed = time.monotonic()
                        wave_gate.output(observed)
                        wave_gate.first(observed)
                        gate.output(observed)
                        gate.first(observed)
                        maximum = max(maximum, observed - last)
                        last = observed
                        row.setdefault('firstOutputSeconds', observed - started)
                        log.write(chunk)
                        log.flush()
            wave_gate.check(time.monotonic())
            gate.check(time.monotonic())
            row['exitCode'] = process.wait(timeout=1)
            text = (job / 'test.log').read_text(errors='replace')
            actual = [line[8:] for line in text.splitlines() if line.startswith('CASE-OK ')]
            row.update(caseOkCount=len(actual), actualCaseNames=actual,
                       inventoryMatches=Counter(actual) == Counter(names),
                       finalOk=final_test_ok(text),
                       sourceUnchanged=hashlib.sha256(file.read_bytes()).hexdigest() == before)
            row['passed'] = (row['exitCode'] == 0 and row['inventoryMatches'] and
                             row['finalOk'] and row['sourceUnchanged'] and
                             '*** ERROR' not in text and 'CASE-FAIL' not in text)
        except Exception as error:
            row['failure'] = repr(error)
            if isinstance(error, GateViolation):
                row['performanceStop'] = error.record
        finally:
            selector.close()
            if process is not None:
                row['cleanup'] = (force_stop(process) if row.get('performanceStop') else reap(process))
                if row['cleanup']['errors'] or not row['cleanup']['reaped']:
                    row['passed'] = False
            row.update(wallSeconds=time.monotonic() - started,
                       maximumOutputGapSeconds=maximum)
            (job / 'result.json').write_text(json.dumps(row, indent=2) + '\n')
        print(json.dumps(dict(testFile=relative, passed=row['passed'],
                              wallSeconds=row['wallSeconds'], failure=row.get('failure'))), flush=True)
        return row

    wave_started = time.monotonic()
    diagnostic_denials = {}
    wave_gate = ProgressiveGate(execution_limits(args.completion_diagnostic), wave_started)
    with ThreadPoolExecutor(max_workers=cores) as pool:
        rows = list(pool.map(run, enumerate(files)))
    elapsed = time.monotonic() - wave_started
    admission = wave_admission(rows, elapsed)
    if wave_gate.first_event is None or wave_gate.first_event > 5:
        admission['failures'].append('whole-task-first-output-over-5-second-ceiling-or-missing')
        admission.update(decision='DENY', admitted=False)
    report = dict(qualified=admission['admitted'] and not args.completion_diagnostic,
                  diagnosticOnly=args.completion_diagnostic,
                  correctnessQualified=admission['correctnessGatePassed'],
                  diagnosticDenials=diagnostic_denials,
                  performanceQualified=(admission['durationGatePassed'] and
                                        wave_gate.first_event is not None and
                                        wave_gate.first_event <= 5),
                  cores=cores, silenceBudgetSeconds=None,
                  policy='whole-task-first-5-complete-112',
                  scheduling='integration-first' if args.integration_first else 'original-file-order',
                  perFileSilenceGate=False, firstOutputSeconds=wave_gate.first_event,
                  wallBudgetSeconds=TEST_CEILING_SECONDS, firstOutputCeilingSeconds=5,
                  executionSafetyCeilingSeconds=wave_gate.limits.complete,
                  waveWallSeconds=elapsed, admission=admission,
                  binarySha256=expected_sha, expectedFiles=39, expectedCases=965, runs=rows,
                  attemptedFiles=sum(row['attempted'] for row in rows),
                  coldArtifactIdentity=cold_identity,
                  artifactScope=('candidate-cold-built-MCP-artifacts' if cold_identity else
                                 'retained-built-MCP-artifacts-not-this-candidate-cold-build'))
    (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({key: report[key] for key in
                      ('qualified', 'waveWallSeconds', 'cores', 'admission')}))
    return 0 if report['qualified'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
