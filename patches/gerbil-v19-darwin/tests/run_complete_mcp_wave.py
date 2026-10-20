"""Frozen whole-task acceptance; no extra per-file silence budget."""
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
from progressive_performance_gate import (GateViolation, Limits, ProgressiveGate, force_stop,
                                         FIRST_LOG_SECONDS, COMPLETE_TEST_SECONDS)

TEST_CEILING_SECONDS = COMPLETE_TEST_SECONDS


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
        failures.append('complete-test-wave-over-frozen-ceiling-or-invalid-duration')
    return dict(decision='DENY' if failures else 'ALLOW', admitted=not failures,
                failures=failures, ceilingSeconds=TEST_CEILING_SECONDS, targetSeconds=TEST_CEILING_SECONDS,
                targetMet=duration, durationGatePassed=duration, correctnessGatePassed=correctness)


def execution_limits(diagnostic):
    # Completion diagnostics retain a safety bound, never a wider admission gate.
    return Limits('complete-test-wave', complete=900 if diagnostic else TEST_CEILING_SECONDS,
                  first=None if diagnostic else FIRST_LOG_SECONDS, silence=None)


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
    parser.add_argument('--driver-bin', type=Path)
    parser.add_argument('--static-object-reuse', action='store_true')
    parser.add_argument('--generated-c-reuse', action='store_true')
    parser.add_argument('--native-generated-c-gsc', action='store_true')
    parser.add_argument('--native-in-process-digests', action='store_true')
    parser.add_argument('--closed-link-profile', type=Path)
    parser.add_argument('--bound-cold-capture', action='store_true')
    parser.add_argument('--bound-single-pass', action='store_true')
    parser.add_argument('--closed-link-producer-proof', action='store_true')
    parser.add_argument('--closed-link-recipe-proof', action='store_true')
    parser.add_argument('--native-object-capture', action='store_true')
    parser.add_argument('--native-object-check', action='store_true')
    parser.add_argument('--fresh-produced-objects', action='store_true')
    parser.add_argument('--planned-producers', action='store_true')
    parser.add_argument('--module-overlay-library', type=Path)
    parser.add_argument('--whole-task-gates', action='store_true')
    parser.add_argument('--integration-first', action='store_true')
    parser.add_argument('--completion-diagnostic', action='store_true')
    args = parser.parse_args()
    if args.closed_link_profile and (not args.native_in_process_digests or args.planned_producers):
        parser.error('closed link requires native compiled digests, without planned singleton producers')
    if args.bound_cold_capture and not args.closed_link_profile:
        parser.error('bound cold capture requires an explicit closed-link profile')
    if args.bound_single_pass and (not args.closed_link_profile or args.bound_cold_capture):
        parser.error('single-pass requires a closed-link profile and excludes cold capture')
    if args.closed_link_producer_proof and not args.bound_single_pass:
        parser.error('producer proof requires the explicit single-pass closed-link candidate')
    if args.closed_link_recipe_proof and not args.closed_link_producer_proof:
        parser.error('recipe proof requires the explicit producer-proof candidate')
    if args.native_object_capture and not (args.bound_single_pass and args.closed_link_profile):
        parser.error('native capture requires an explicit bound single-pass closed-link candidate')
    if args.native_object_check and not args.native_object_capture:
        parser.error('native check requires the explicit native-capture candidate')
    if args.fresh_produced_objects and (not args.closed_link_profile or args.closed_link_producer_proof):
        parser.error('fresh objects require a closed-link profile and exclude eager producer proof')
    if args.native_in_process_digests and not args.native_generated_c_gsc:
        parser.error('compiled digests require native GSC')
    if args.planned_producers and not (args.native_in_process_digests and args.module_overlay_library):
        parser.error('planned producers require compiled digests and a compiled module overlay')
    if args.module_overlay_library and not args.planned_producers:
        parser.error('module overlay requires the explicit planned producer experiment')
    if args.native_generated_c_gsc and (args.generated_c_reuse or args.driver_bin is None):
        parser.error('native GSC requires an isolated driver, without the dynamic adapter')
    if not args.whole_task_gates:
        parser.error('explicit whole-task gate policy selection required')
    if args.static_object_reuse and args.driver_bin is None:
        parser.error('static-object reuse requires an isolated candidate driver')
    root = Path(__file__).resolve().parents[3]
    binary, home, project, out = [getattr(args, key).resolve() for key in
                                  ('binary', 'home', 'project', 'output')]
    if any(not p.is_relative_to(root / '.data') for p in (binary, home, project, out)):
        parser.error('isolated project .data paths required')
    overlay = args.module_overlay_library.absolute() if args.module_overlay_library else None
    overlay_identity = {}
    if overlay:
        from experiment_framework.module_overlay import module_overlay_identity
        if not overlay.resolve().is_relative_to(root / '.data'):
            parser.error('isolated module overlay required')
        overlay_identity = module_overlay_identity(overlay, 'std/make')
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
    if args.driver_bin:
        driver = args.driver_bin.absolute()
        if not driver.resolve().is_relative_to(root / '.data'):
            raise ValueError('isolated candidate driver required')
    driver_sha = hashlib.sha256((driver / 'gambuild-C').read_bytes()).hexdigest()
    if driver_sha != cold['candidateDriverSha256']:
        raise ValueError('test driver differs from cold-build driver')
    base.update(GERBIL_HOME=str(home), GERBIL_PATH=str(project / '.gerbil'),
                GERBIL_LOADPATH=f'{project / ".gerbil/lib"}:{home / "lib"}:{project}',
                GERBIL_GSC=str(driver / 'gsc'), GERBIL_GCC=base['GERBIL_GNU_GCC'],
                GERBIL_BUILD_CORES=str(cores), GAMBIT_EMBEDDED_NATIVE='0',
                GAMBOPT=f'~~bin={driver},~~lib={home / "lib"},~~include={home / "include"}',
                GERBIL_MCP_BIN=str(project / '.gerbil/bin/gerbil-mcp'),
                GERBIL_MCP_MODE='full')
    if args.static_object_reuse:
        base['GAMBIT_DARWIN_STATIC_OBJECT_REUSE'] = '1'
    if args.generated_c_reuse != cold.get('generatedCReuseEnabled', False):
        raise ValueError('generated-C option differs from cold build')
    if args.generated_c_reuse:
        for name, sha in cold['generatedCIdentity'].items():
            if hashlib.sha256((driver / name).read_bytes()).hexdigest() != sha:
                raise ValueError('generated-C tool differs from cold build: ' + name)
        base['GAMBIT_DARWIN_GENERATED_C_REUSE'] = '1'
    native_identity = {}
    if args.native_generated_c_gsc != cold.get('nativeGeneratedCGscEnabled', False):
        raise ValueError('native GSC option differs from cold build')
    if args.native_in_process_digests != cold.get('nativeInProcessDigestsEnabled', False):
        raise ValueError('compiled digest option differs from cold build')
    if args.planned_producers != cold.get('plannedProducersEnabled', False):
        raise ValueError('producer policy differs from cold build')
    if bool(args.closed_link_profile) != cold.get('closedLinkReuseEnabled', False):
        raise ValueError('closed link policy differs from cold build')
    if args.bound_cold_capture != cold.get('boundColdCaptureEnabled', False):
        raise ValueError('bound cold capture policy differs from cold build')
    if args.bound_single_pass != cold.get('boundSinglePassEnabled', False):
        raise ValueError('single-pass policy differs from cold build')
    if args.closed_link_producer_proof != cold.get('closedLinkProducerProofEnabled', False):
        raise ValueError('producer proof policy differs from cold build')
    if args.closed_link_recipe_proof != cold.get('closedLinkRecipeProofEnabled', False):
        raise ValueError('recipe proof policy differs from cold build')
    if args.native_object_capture != cold.get('nativeObjectCaptureEnabled', False):
        raise ValueError('native capture policy differs from cold build')
    if args.native_object_check != cold.get('nativeObjectCheckEnabled', False):
        raise ValueError('native check policy differs from cold build')
    if args.fresh_produced_objects != cold.get('freshProducedObjectsEnabled', False):
        raise ValueError('fresh-object policy differs from cold build')
    if overlay_identity != cold.get('moduleOverlayIdentity', {}):
        raise ValueError('module overlay differs from cold build')
    if overlay:
        base['GERBIL_LOADPATH'] = str(overlay) + ':' + base['GERBIL_LOADPATH']
    base.pop('GAMBIT_GENERATED_C_PRODUCER_INDEX', None)
    base.pop('GAMBIT_GENERATED_C_BATCH_DIGESTS', None)
    base.pop('GAMBIT_GENERATED_C_IN_PROCESS_DIGESTS', None)
    base.pop('GAMBIT_DARWIN_CLOSED_LINK_RECIPE_PROOF', None)
    base.pop('GAMBIT_DARWIN_CLOSED_LINK_MEMBER_PROOF', None)
    base.pop('GAMBIT_DARWIN_CLOSED_LINK_MEMBER_TOOLS_BATCH', None)
    if args.native_generated_c_gsc:
        from native_generated_c_profile import verify_native_profile
        native_identity = verify_native_profile(root, driver, in_process_digests=args.native_in_process_digests,
                                               planned_producers=args.planned_producers,
                                               closed_link_profile=args.closed_link_profile, runtime=home)
        if native_identity != cold['nativeGscIdentity']:
            raise ValueError('native GSC profile differs from cold build')
        base['GAMBIT_DARWIN_NATIVE_GENERATED_C'] = '1'
        base['GAMBIT_GENERATED_C_BATCH_DIGESTS'] = '1'
        index = project / '.native-generated-c-index'
        index.mkdir(exist_ok=True)
        base['GAMBIT_GENERATED_C_PRODUCER_INDEX'] = str(index)
    if args.closed_link_profile:
        base.pop('GAMBIT_DARWIN_NATIVE_GENERATED_C', None)
        base.pop('GAMBIT_GENERATED_C_PRODUCER_INDEX', None)
        base.pop('GAMBIT_GENERATED_C_BATCH_DIGESTS', None)
        base['GAMBIT_DARWIN_CLOSED_LINK_REUSE'] = '1'
    if args.native_in_process_digests:
        base['GAMBIT_GENERATED_C_IN_PROCESS_DIGESTS'] = '1'
    if args.bound_cold_capture:
        base['GAMBIT_DARWIN_BOUND_COLD_CAPTURE'] = '1'
    if args.bound_single_pass:
        base['GAMBIT_DARWIN_BOUND_SINGLE_PASS'] = '1'
    if args.closed_link_producer_proof:
        base['GAMBIT_DARWIN_CLOSED_LINK_PRODUCER_PROOF'] = '1'
    if args.closed_link_recipe_proof:
        base['GAMBIT_DARWIN_CLOSED_LINK_RECIPE_PROOF'] = '1'
    if args.native_object_capture:
        base['GAMBIT_DARWIN_NATIVE_OBJECT_CAPTURE'] = '1'
    if args.native_object_check:
        base['GAMBIT_DARWIN_NATIVE_OBJECT_CHECK'] = '1'
    if args.fresh_produced_objects:
        base['GAMBIT_DARWIN_CLOSED_LINK_FRESH_OBJECTS'] = '1'

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
            selected_gsc_sha = native_identity.get('gsc', construction['gscSha256'])
            if gsc != (driver / 'gsc').resolve(strict=True) or gsc_sha != selected_gsc_sha:
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
    if args.native_generated_c_gsc:
        try:
            verify_native_profile(root, driver, in_process_digests=args.native_in_process_digests,
                                  planned_producers=args.planned_producers,
                                  closed_link_profile=args.closed_link_profile, runtime=home)
            if overlay and module_overlay_identity(overlay, 'std/make') != overlay_identity:
                raise ValueError('module overlay changed during complete testing')
        except Exception as caught:
            admission['failures'].append(repr(caught))
            admission.update(decision='DENY', admitted=False)
    if wave_gate.first_event is None or wave_gate.first_event > FIRST_LOG_SECONDS:
        admission['failures'].append('whole-task-first-output-over-frozen-ceiling-or-missing')
        admission.update(decision='DENY', admitted=False)
    report = dict(qualified=admission['admitted'] and not args.completion_diagnostic,
                  diagnosticOnly=args.completion_diagnostic,
                  correctnessQualified=admission['correctnessGatePassed'],
                  diagnosticDenials=diagnostic_denials,
                  performanceQualified=(admission['durationGatePassed'] and
                                        wave_gate.first_event is not None and
                                        wave_gate.first_event <= FIRST_LOG_SECONDS),
                  cores=cores, silenceBudgetSeconds=None,
                  policy='frozen-mcp-v4-whole-task',
                  scheduling='integration-first' if args.integration_first else 'original-file-order',
                  perFileSilenceGate=False, firstOutputSeconds=wave_gate.first_event,
                  wallBudgetSeconds=TEST_CEILING_SECONDS, firstOutputCeilingSeconds=FIRST_LOG_SECONDS,
                  executionSafetyCeilingSeconds=wave_gate.limits.complete,
                  waveWallSeconds=elapsed, admission=admission,
                  binarySha256=expected_sha, expectedFiles=39, expectedCases=965, runs=rows,
                  selectedDriverBin=str(driver.relative_to(root)), selectedDriverSha256=driver_sha,
                  staticObjectReuseEnabled=args.static_object_reuse,
                  nativeGeneratedCGscEnabled=args.native_generated_c_gsc,
                  nativeInProcessDigestsEnabled=args.native_in_process_digests,
                  plannedProducersEnabled=args.planned_producers,
                  moduleOverlayIdentity=overlay_identity,
                  nativeGscIdentity=native_identity,
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
