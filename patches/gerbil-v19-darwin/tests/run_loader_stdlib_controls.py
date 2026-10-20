"""Unmodified standard-library tests for the isolated loader diagnostic."""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess
import time

from bazel_host_environment import build_environment
from probe_retained_native_loader import FROZEN, digest
from progressive_performance_gate import force_stop


def completed_cases(lines):
    started = [line.removeprefix('CASE ') for line in lines if line.startswith('CASE ')]
    completed = [line.removeprefix('CASE-OK ') for line in lines if line.startswith('CASE-OK ')]
    if not started or Counter(started) != Counter(completed) or lines[-1:] != ['OK']:
        raise ValueError('all original test cases and final OK required')
    if any(line.startswith(('*** ERROR', 'ERROR ', 'CASE-FAIL', 'SUITE-FAIL', 'MODULE-FAIL',
                            'HARNESS-FAIL')) for line in lines):
        raise ValueError('failed test status')
    return completed


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--probe', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    probe, output = args.probe.resolve(), args.output.resolve()
    if not all(path.is_relative_to(root / '.data') for path in (probe, output)) or output.exists():
        parser.error('persistent diagnostic input and fresh output required')
    receipt = json.loads((probe.parent / 'report.json').read_text())
    if not receipt['qualified'] or digest(probe) != receipt['binarySha256']:
        raise ValueError('selected diagnostic identity changed')
    original = root / '.data/d1510-reader-whitespace-native-v2/gerbil'
    if digest(original) != FROZEN:
        raise ValueError('retained binary changed')
    source = root / '.data/d1391-runtime-object-source/src/std'
    owners = ('list/list-test.ss', 'encoding/json/json-test.ss')
    inputs = {owner: digest(source / owner) for owner in owners}
    home = root / '.data/d1510-mcp-test-source-home-v2/build'
    env = build_environment()
    cores = int(subprocess.check_output(['sysctl', '-n', 'hw.physicalcpu'], text=True))
    for key in tuple(env):
        if key.startswith(('GAMBIT_DARWIN_', 'GERBIL_MCP_')):
            env.pop(key)
    env.pop('GERBIL_BUILD_PREFIX', None)
    output.mkdir()
    (output / 'package-home').mkdir()
    env.update(GERBIL_HOME=str(home), GERBIL_PATH=str(output / 'package-home'),
               GERBIL_LOADPATH=str(home / 'lib'), GERBIL_BUILD_CORES=str(cores),
               GAMBIT_EMBEDDED_NATIVE='0')
    report = dict(qualified=False, performanceQualified=False, productionAdmitted=False,
                  fullSuiteQualified=False, scope='two-original-stdlib-test-files-loader-controls',
                  workers=cores, sourceHashes=inputs, runs=[])

    def execute(role, owner):
        name = role + '-' + owner.replace('/', '-')
        binary = original if role == 'control' else probe
        log_path = output / (name + '.log')
        start = time.monotonic()
        with log_path.open('w') as log:
            child = subprocess.Popen([str(binary), 'test', '-v', '5', str(source / owner)],
                                     cwd=output, env=env, stdout=log, stderr=subprocess.STDOUT,
                                     start_new_session=True)
            try:
                child.wait(timeout=30)
            finally:
                if child.poll() is None:
                    force_stop(child)
        lines = log_path.read_text().splitlines()
        try:
            cases = completed_cases(lines)
        except ValueError:
            cases = []
        return dict(role=role, owner=owner, wallSeconds=time.monotonic() - start,
                    exitCode=child.returncode,
                    cases=cases, passed=child.returncode == 0 and bool(cases))

    try:
        start = time.monotonic()
        with ThreadPoolExecutor(max_workers=cores) as pool:
            futures = [pool.submit(execute, role, owner)
                       for role in ('control', 'probe') for owner in owners]
            for future in futures:
                row = future.result()
                report['runs'].append(row)
                print(json.dumps({k: v for k, v in row.items() if k != 'cases'}), flush=True)
        report['waveWallSeconds'] = time.monotonic() - start
        report['sourceUnchanged'] = inputs == {owner: digest(source / owner) for owner in owners}
        report['binaryUnchanged'] = digest(original) == FROZEN and digest(probe) == receipt['binarySha256']
        report['caseIdentitiesMatch'] = all(Counter(next(row['cases'] for row in report['runs']
            if row['owner'] == owner and row['role'] == 'control')) == Counter(next(row['cases']
            for row in report['runs'] if row['owner'] == owner and row['role'] == 'probe')) for owner in owners)
        report['qualified'] = report['sourceUnchanged'] and report['binaryUnchanged'] and report['caseIdentitiesMatch'] and all(
            row['passed'] for row in report['runs']) and len(report['runs']) == 4
    finally:
        (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    return 0 if report['qualified'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
