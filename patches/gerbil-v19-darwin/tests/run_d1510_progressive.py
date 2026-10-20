"""Retained D1510 recipe, hard runtime gates, then selected-toolchain tests."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

from progressive_performance_gate import (
    GateViolation, Limits, ProgressiveGate, force_stop, instrument_cold_controller,
    FIRST_LOG_SECONDS, COMPLETE_SECONDS,
)


def cold_admission(report, ceiling=COMPLETE_SECONDS):
    if type(ceiling) is not int or not 0 < ceiling <= COMPLETE_SECONDS:
        raise ValueError('cannot widen the frozen MCP cold-build ceiling')
    failures = []
    if not report.get('qualified') or not report.get('sourceUnchanged') or not report.get('runs'):
        failures.append('cold-correctness-or-source-identity')
    for index, row in enumerate(report.get('runs', [])):
        for key, limit in (('firstCompileSeconds', FIRST_LOG_SECONDS), ('buildWallSeconds', ceiling)):
            value = row.get(key)
            if type(value) not in (int, float) or not 0 < value <= limit:
                failures.append(f'run-{index}-{key}')
        if row.get('performanceStops') or not row.get('passed'):
            failures.append(f'run-{index}-runtime-or-correctness-stop')
    return dict(decision='DENY' if failures else 'ALLOW', admitted=not failures,
                failures=failures, firstCompileCeilingSeconds=FIRST_LOG_SECONDS,
                completeBuildCeilingSeconds=ceiling)


def candidate_ceiling(root, binary_digest, requested):
    lock_path = root / 'patches/gerbil-v19-darwin/receipts/d1510-mcp-v4-performance-lock.json'
    lock = json.loads(lock_path.read_text())
    ceiling = lock['limitsSeconds']['completeBuild']
    if requested is not None and (type(requested) is not int or not 0 < requested <= ceiling):
        raise ValueError('no candidate may widen the frozen MCP ceiling')
    return ceiling if requested is None else requested


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--binary', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--test-home', type=Path, required=True)
    parser.add_argument('--build-ceiling', type=int)
    parser.add_argument('--cold-runs', type=int, choices=(1, 2, 3), default=1)
    parser.add_argument('--cold-only', action='store_true')
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
    parser.add_argument('--gsc-entry-trace', action='store_true')
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
    if args.native_generated_c_gsc and args.generated_c_reuse:
        parser.error('native GSC and rejected dynamic adapter are mutually exclusive')
    if (args.static_object_reuse or args.generated_c_reuse or args.native_generated_c_gsc) and args.driver_bin is None:
        parser.error('reuse requires an isolated candidate driver')
    if args.gsc_entry_trace and not (args.generated_c_reuse and args.cold_only):
        parser.error('GSC entry tracing is diagnostic cold-only, with generated-C adapter')
    root = Path(__file__).resolve().parents[3]
    binary, output, home = (p.resolve() for p in (args.binary, args.output, args.test_home))
    if any(not p.is_relative_to(root / '.data') for p in (binary, output, home)):
        parser.error('persistent isolated .data paths required')
    if output.exists():
        parser.error('fresh output directory required')
    overlay = args.module_overlay_library.absolute() if args.module_overlay_library else None
    overlay_identity = {}
    if overlay:
        from experiment_framework.module_overlay import module_overlay_identity
        if not overlay.resolve().is_relative_to(root / '.data'):
            parser.error('isolated module overlay required')
        overlay_identity = module_overlay_identity(overlay, 'std/make')
    args.build_ceiling = candidate_ceiling(
        root, hashlib.sha256(binary.read_bytes()).hexdigest(), args.build_ceiling)
    driver = root / '.data/d1510-shell-substitution/bin'
    original = root / '.data/d1391-runtime-object-source/build/bin'
    if (driver / 'gsc').read_bytes() != (original / 'gsc').read_bytes():
        raise ValueError('selected GSC identity drift')
    if not json.loads((driver.parent / 'check.json').read_text())['commandParity']:
        raise ValueError('driver command parity failed')
    if not json.loads((driver.parent / 'real-object.json').read_text())['qualified']:
        raise ValueError('driver real object check failed')
    digest = hashlib.sha256((driver / 'gambuild-C').read_bytes()).hexdigest()
    if digest != json.loads((driver.parent / 'report.json').read_text())['candidateDriverSha256']:
        raise ValueError('selected driver drift')
    if args.driver_bin:
        driver = args.driver_bin.absolute()
        if not driver.resolve().is_relative_to(root / '.data'):
            raise ValueError('isolated candidate driver required')
        compiler = driver / ('gsc-original' if args.generated_c_reuse or args.native_generated_c_gsc else 'gsc')
        if compiler.read_bytes() != (original / 'gsc').read_bytes():
            raise ValueError('candidate GSC identity drift')
        candidate = driver / 'gambuild-C'
        if (not candidate.is_file() or not os.access(candidate, os.X_OK)
                or not candidate.resolve().is_relative_to(root / '.data')):
            raise ValueError('candidate driver missing')
        digest = hashlib.sha256((driver / 'gambuild-C').read_bytes()).hexdigest()
    generation_files = ['gsc', 'gsc-original', 'gambit-generated-c-reads.scm',
                        'gambit-generated-c-closure.scm', 'gambit-generated-c-adapter.scm'] if args.generated_c_reuse else []
    if args.generated_c_reuse:
        tests = Path(__file__).parent
        for name, source_name in [('gsc', 'gambit-generated-c-dispatch.sh'),
                                 *[(name, name) for name in generation_files[2:]]]:
            if (driver / name).read_bytes() != (tests / source_name).read_bytes():
                raise ValueError('generated-C adapter source drift: ' + name)
    generation_identity = {name: hashlib.sha256((driver / name).read_bytes()).hexdigest()
                           for name in generation_files}
    native_identity = {}
    if args.native_generated_c_gsc:
        from native_generated_c_profile import verify_native_profile
        native_identity = verify_native_profile(root, driver, in_process_digests=args.native_in_process_digests,
                                               planned_producers=args.planned_producers,
                                               closed_link_profile=args.closed_link_profile, runtime=home)
    controller = root / '.data/d1395-mcp-runtime-object-ab.py'
    source = instrument_cold_controller(controller.read_text(), args.build_ceiling)
    roles_anchor = "    roles = ('baseline', 'candidate', 'candidate', 'baseline') if args.roles == 'abba' else ('candidate',)"
    if source.count(roles_anchor) != 1:
        raise ValueError('retained roles anchor drift')
    source = source.replace(roles_anchor, f"    roles = ('candidate',) * {args.cold_runs}", 1)
    row_anchor = '        print(json.dumps(row), flush=True)'
    if source.count(row_anchor) != 1:
        raise ValueError('retained result anchor drift')
    source = source.replace(row_anchor, row_anchor + "\n        if not row['passed']:\n            break", 1)
    anchor = '    return env\n'
    if source.count(anchor) != 1:
        raise ValueError('environment anchor drift')
    source = source.replace(anchor, f'''    driver_bin = ROOT / {str(driver.relative_to(root))!r}
    env['GERBIL_GSC'] = str(driver_bin / 'gsc')
    env['GAMBOPT'] = f'~~bin={{driver_bin}},~~lib={{home / "lib"}},~~include={{home / "include"}}'
    if {bool(overlay)!r}:
        env['GERBIL_LOADPATH'] = {str(overlay)!r} + ':' + env['GERBIL_LOADPATH']
    {"env['GAMBIT_DARWIN_STATIC_OBJECT_REUSE'] = '1'" if args.static_object_reuse else "pass"}
    {"env['GAMBIT_DARWIN_GENERATED_C_REUSE'] = '1'" if args.generated_c_reuse else "env.pop('GAMBIT_DARWIN_GENERATED_C_REUSE', None)"}
    env.pop('GAMBIT_GENERATED_C_PRODUCER_INDEX', None)
    env.pop('GAMBIT_GENERATED_C_BATCH_DIGESTS', None)
    env.pop('GAMBIT_GENERATED_C_IN_PROCESS_DIGESTS', None)
    env.pop('GAMBIT_DARWIN_CLOSED_LINK_REUSE', None)
    env.pop('GAMBIT_DARWIN_BOUND_COLD_CAPTURE', None)
    env.pop('GAMBIT_DARWIN_BOUND_SINGLE_PASS', None)
    env.pop('GAMBIT_DARWIN_CLOSED_LINK_PRODUCER_PROOF', None)
    env.pop('GAMBIT_DARWIN_CLOSED_LINK_RECIPE_PROOF', None)
    env.pop('GAMBIT_DARWIN_CLOSED_LINK_MEMBER_PROOF', None)
    env.pop('GAMBIT_DARWIN_CLOSED_LINK_MEMBER_TOOLS_BATCH', None)
    env.pop('GAMBIT_DARWIN_NATIVE_OBJECT_CAPTURE', None)
    env.pop('GAMBIT_DARWIN_NATIVE_OBJECT_CHECK', None)
    env.pop('GAMBIT_DARWIN_CLOSED_LINK_FRESH_OBJECTS', None)
    {"env['GAMBIT_DARWIN_NATIVE_GENERATED_C'] = '1'" if args.native_generated_c_gsc else "env.pop('GAMBIT_DARWIN_NATIVE_GENERATED_C', None)"}
    if {args.native_generated_c_gsc!r}:
        index = PROJECT / '.native-generated-c-index'
        index.mkdir(exist_ok=True)
        env['GAMBIT_GENERATED_C_PRODUCER_INDEX'] = str(index)
        env['GAMBIT_GENERATED_C_BATCH_DIGESTS'] = '1'
    if {bool(args.closed_link_profile)!r}:
        env.pop('GAMBIT_DARWIN_NATIVE_GENERATED_C', None)
        env.pop('GAMBIT_GENERATED_C_PRODUCER_INDEX', None)
        env.pop('GAMBIT_GENERATED_C_BATCH_DIGESTS', None)
        env['GAMBIT_DARWIN_CLOSED_LINK_REUSE'] = '1'
    if {args.native_in_process_digests!r}:
        env['GAMBIT_GENERATED_C_IN_PROCESS_DIGESTS'] = '1'
    if {args.bound_cold_capture!r}:
        env['GAMBIT_DARWIN_BOUND_COLD_CAPTURE'] = '1'
    if {args.bound_single_pass!r}:
        env['GAMBIT_DARWIN_BOUND_SINGLE_PASS'] = '1'
    if {args.closed_link_producer_proof!r}:
        env['GAMBIT_DARWIN_CLOSED_LINK_PRODUCER_PROOF'] = '1'
    if {args.closed_link_recipe_proof!r}:
        env['GAMBIT_DARWIN_CLOSED_LINK_RECIPE_PROOF'] = '1'
    if {args.native_object_capture!r}:
        env['GAMBIT_DARWIN_NATIVE_OBJECT_CAPTURE'] = '1'
    if {args.native_object_check!r}:
        env['GAMBIT_DARWIN_NATIVE_OBJECT_CHECK'] = '1'
    if {args.fresh_produced_objects!r}:
        env['GAMBIT_DARWIN_CLOSED_LINK_FRESH_OBJECTS'] = '1'
    return env
''')
    source = source.replace('report = dict(qualified=False,',
                            f'report = dict(closedLinkRecipeProofEnabled={args.closed_link_recipe_proof!r}, freshProducedObjectsEnabled={args.fresh_produced_objects!r}, nativeObjectCheckEnabled={args.native_object_check!r}, nativeObjectCaptureEnabled={args.native_object_capture!r}, closedLinkProducerProofEnabled={args.closed_link_producer_proof!r}, boundSinglePassEnabled={args.bound_single_pass!r}, boundColdCaptureEnabled={args.bound_cold_capture!r}, closedLinkReuseEnabled={bool(args.closed_link_profile)!r}, plannedProducersEnabled={args.planned_producers!r}, moduleOverlayIdentity={overlay_identity!r}, nativeInProcessDigestsEnabled={args.native_in_process_digests!r}, nativeGeneratedCGscEnabled={args.native_generated_c_gsc!r}, nativeGscIdentity={native_identity!r}, generatedCReuseEnabled={args.generated_c_reuse!r}, generatedCIdentity={generation_identity!r}, staticObjectReuseEnabled={args.static_object_reuse!r}, candidateDriverBin={str(driver.relative_to(root))!r}, candidateDriverSha256={digest!r}, qualified=False,', 1)
    source = source.replace("paths = [home / 'bin/gsc', home / 'bin/gambuild-C',",
                            "paths = [Path(local_env['GERBIL_GSC']), Path(local_env['GERBIL_GSC']).parent / 'gambuild-C',")
    if args.gsc_entry_trace:
        anchor = '    local_env = environment(source, role)\n'
        if source.count(anchor) != 1:
            raise ValueError('GSC trace phase anchor drift')
        source = source.replace(anchor, anchor + "    local_env['GAMBIT_GENERATION_TRACE'] = str(directory / (name + '-gsc-entry.log'))\n", 1)
    namespace = dict(__file__=str(controller), __name__='__main__',
                     ProgressiveGate=ProgressiveGate, Limits=Limits,
                     GateViolation=GateViolation, force_stop=force_stop)
    old_argv = sys.argv
    sys.argv = [str(controller), '--candidate-binary', str(binary), '--roles', 'candidate',
                '--capture-configuration', '--require-performance-ceiling', '--output', str(output)]
    error = None
    try:
        exec(compile(source, str(controller), 'exec'), namespace)
    except (Exception, SystemExit) as caught:
        error = repr(caught)
    finally:
        sys.argv = old_argv
    report_path = output / 'report.json'
    report = json.loads(report_path.read_text()) if report_path.exists() else {}
    admission = cold_admission(report, args.build_ceiling)
    if any(hashlib.sha256((driver / name).read_bytes()).hexdigest() != sha
           for name, sha in generation_identity.items()):
        error = 'generated-C adapter identity changed during cold build'
    if error:
        admission.update(decision='DENY', admitted=False)
        admission['failures'].append(error)
    if args.native_generated_c_gsc:
        try:
            verify_native_profile(root, driver, in_process_digests=args.native_in_process_digests,
                                  planned_producers=args.planned_producers,
                                  closed_link_profile=args.closed_link_profile, runtime=home)
            if overlay and module_overlay_identity(overlay, 'std/make') != overlay_identity:
                raise ValueError('module overlay changed during cold build')
        except Exception as caught:
            admission.update(decision='DENY', admitted=False)
            admission['failures'].append(repr(caught))
    pipeline = dict(cold=admission, test=dict(decision='SKIP', reason='cold-gate-not-admitted'),
                    decision='DENY', qualified=False)
    if args.gsc_entry_trace:
        pipeline['diagnosticOnly'] = True
        pipeline['gscEntryCounts'] = {str(path.relative_to(output)): len(path.read_text().splitlines())
                                     for path in output.glob('*-candidate/*-gsc-entry.log')}
    output.mkdir(exist_ok=True)
    (output / 'progressive-admission.json').write_text(json.dumps(pipeline, indent=2) + '\n')
    if not admission['admitted']:
        print(json.dumps(pipeline), flush=True)
        return 1
    if args.cold_only:
        pipeline.update(decision='DIAGNOSTIC_ONLY' if args.gsc_entry_trace else 'COLD_ONLY_ALLOW',
                        coldQualified=not args.gsc_entry_trace,
                        test=dict(decision='SKIP', reason='explicit-cold-repeat-only'),
                        qualified=False)
        (output / 'progressive-admission.json').write_text(json.dumps(pipeline, indent=2) + '\n')
        print(json.dumps(pipeline), flush=True)
        return 0
    project = output / '0-candidate/project'
    fixture = root / 'patches/gerbil-v19-darwin/receipts/mcp-selected-toolchain-fixtures.patch'
    try:
        if hashlib.sha256((driver / 'gambuild-C').read_bytes()).hexdigest() != digest:
            raise ValueError('driver changed after cold build')
        subprocess.run(['git', 'apply', '--check', str(fixture)], cwd=project, check=True)
        subprocess.run(['git', 'apply', str(fixture)], cwd=project, check=True)
        test_process = subprocess.run([
            sys.executable, str(Path(__file__).with_name('run_complete_mcp_wave.py')),
            '--binary', str(binary), '--home', str(home), '--project', str(project),
            '--output', str(output / 'tests'), '--cold-report', str(report_path),
            '--whole-task-gates', '--driver-bin', str(driver),
            *(['--static-object-reuse'] if args.static_object_reuse else []),
            *(['--generated-c-reuse'] if args.generated_c_reuse else []),
            *(['--native-generated-c-gsc'] if args.native_generated_c_gsc else []),
            *(['--native-in-process-digests'] if args.native_in_process_digests else []),
            *(['--closed-link-profile', str(args.closed_link_profile)] if args.closed_link_profile else []),
            *(['--bound-cold-capture'] if args.bound_cold_capture else []),
            *(['--bound-single-pass'] if args.bound_single_pass else []),
            *(['--closed-link-producer-proof'] if args.closed_link_producer_proof else []),
            *(['--closed-link-recipe-proof'] if args.closed_link_recipe_proof else []),
            *(['--native-object-capture'] if args.native_object_capture else []),
            *(['--native-object-check'] if args.native_object_check else []),
            *(['--fresh-produced-objects'] if args.fresh_produced_objects else []),
            *(['--planned-producers', '--module-overlay-library', str(overlay)] if args.planned_producers else [])], check=False)
        test_report = json.loads((output / 'tests/report.json').read_text())
        pipeline['test'] = test_report['admission']
        pipeline['qualified'] = (test_process.returncode == 0 and
                                 test_report['qualified'] and pipeline['test']['admitted'])
    except Exception as caught:
        pipeline['test'] = dict(decision='DENY', admitted=False, failure=repr(caught))
    pipeline['decision'] = 'ALLOW' if pipeline['qualified'] else 'DENY'
    (output / 'progressive-admission.json').write_text(json.dumps(pipeline, indent=2) + '\n')
    print(json.dumps(pipeline), flush=True)
    return 0 if pipeline['qualified'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
