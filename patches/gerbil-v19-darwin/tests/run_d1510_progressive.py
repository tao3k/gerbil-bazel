"""Retained D1510 recipe, hard runtime gates, then selected-toolchain tests."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from progressive_performance_gate import (
    GateViolation, Limits, ProgressiveGate, force_stop, instrument_cold_controller,
)


def cold_admission(report, ceiling=52):
    if type(ceiling) is not int or ceiling not in (50, 52):
        raise ValueError('only existing or tighter cold-build ceiling allowed')
    failures = []
    if not report.get('qualified') or not report.get('sourceUnchanged') or not report.get('runs'):
        failures.append('cold-correctness-or-source-identity')
    for index, row in enumerate(report.get('runs', [])):
        for key, limit in (('firstCompileSeconds', 5), ('buildWallSeconds', ceiling)):
            value = row.get(key)
            if type(value) not in (int, float) or not 0 < value <= limit:
                failures.append(f'run-{index}-{key}')
        if row.get('performanceStops') or not row.get('passed'):
            failures.append(f'run-{index}-runtime-or-correctness-stop')
    return dict(decision='DENY' if failures else 'ALLOW', admitted=not failures,
                failures=failures, firstCompileCeilingSeconds=5,
                completeBuildCeilingSeconds=ceiling)


def candidate_ceiling(root, binary_digest, requested):
    lock_path = root / 'patches/gerbil-v19-darwin/receipts/d1510-reader-batch-50-baseline.json'
    lock = json.loads(lock_path.read_text())
    assert lock['ceilingSeconds'] == 50
    old_lock = json.loads((root / 'patches/gerbil-v19-darwin/receipts/d1510-source-loader-49-baseline.json').read_text())
    historical = binary_digest == old_lock['candidateBinarySha256']
    if not historical and requested not in (None, 50):
        raise ValueError('new candidates cannot widen the 50-second ceiling')
    return (52 if historical else 50) if requested is None else requested


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--binary', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--test-home', type=Path, required=True)
    parser.add_argument('--build-ceiling', type=int, choices=(50, 52))
    parser.add_argument('--cold-runs', type=int, choices=(1, 2, 3), default=1)
    parser.add_argument('--cold-only', action='store_true')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    binary, output, home = (p.resolve() for p in (args.binary, args.output, args.test_home))
    if any(not p.is_relative_to(root / '.data') for p in (binary, output, home)):
        parser.error('persistent isolated .data paths required')
    if output.exists():
        parser.error('fresh output directory required')
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
    source = source.replace(anchor, '''    driver_bin = ROOT / '.data/d1510-shell-substitution/bin'
    env['GERBIL_GSC'] = str(driver_bin / 'gsc')
    env['GAMBOPT'] = f'~~bin={driver_bin},~~lib={home / "lib"},~~include={home / "include"}'
    return env
''')
    source = source.replace('report = dict(qualified=False,',
                            f'report = dict(candidateDriverSha256={digest!r}, qualified=False,', 1)
    source = source.replace("paths = [home / 'bin/gsc', home / 'bin/gambuild-C',",
                            "paths = [Path(local_env['GERBIL_GSC']), Path(local_env['GERBIL_GSC']).parent / 'gambuild-C',")
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
    if error:
        admission.update(decision='DENY', admitted=False)
        admission['failures'].append(error)
    pipeline = dict(cold=admission, test=dict(decision='SKIP', reason='cold-gate-not-admitted'),
                    decision='DENY', qualified=False)
    output.mkdir(exist_ok=True)
    (output / 'progressive-admission.json').write_text(json.dumps(pipeline, indent=2) + '\n')
    if not admission['admitted']:
        print(json.dumps(pipeline), flush=True)
        return 1
    if args.cold_only:
        pipeline.update(decision='COLD_ONLY_ALLOW', coldQualified=True,
                        test=dict(decision='SKIP', reason='explicit-cold-repeat-only'),
                        qualified=False)
        (output / 'progressive-admission.json').write_text(json.dumps(pipeline, indent=2) + '\n')
        print(json.dumps(pipeline), flush=True)
        return 0
    project = output / '0-candidate/project'
    fixture = root / 'patches/gerbil-v19-darwin/receipts/mcp-selected-toolchain-fixtures.patch'
    try:
        subprocess.run(['git', 'apply', '--check', str(fixture)], cwd=project, check=True)
        subprocess.run(['git', 'apply', str(fixture)], cwd=project, check=True)
        test_process = subprocess.run([
            sys.executable, str(Path(__file__).with_name('run_complete_mcp_wave.py')),
            '--binary', str(binary), '--home', str(home), '--project', str(project),
            '--output', str(output / 'tests'), '--cold-report', str(report_path),
            '--whole-task-gates'], check=False)
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
