"""Isolated original std/make construction and std/test artifact qualification."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import shutil
import threading
import time

from bazel_host_environment import build_environment
from native_object_manifest import digest
from progressive_performance_gate import Limits, ProgressiveGate
from run_loader_stdlib_controls import completed_cases
from experiment_framework.context import data_path, hardware_workers, retained_47
from experiment_framework.process import execute


def selected_driver(root, home, override=None):
    driver = data_path(root, override or home / 'bin/gambuild-C')
    if not driver.is_file() or not os.access(driver, os.X_OK):
        raise ValueError('executable isolated Gambit driver required')
    return driver


def qualify_test_result(row, owner, lines):
    result = dict(row, owner=owner, cases=None, caseVerificationPassed=False)
    try:
        result['cases'] = completed_cases(lines)
    except ValueError as error:
        result.update(passed=False, caseVerificationError=str(error))
    else:
        result['caseVerificationPassed'] = True
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--binary', type=Path)
    parser.add_argument('--gambuild-driver', type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    output = data_path(root, args.output, fresh=True)
    toolchain = retained_47(root, args.binary)
    binary = toolchain.binary
    source = root / '.data/d935-staging-source/src/std'
    original_home = toolchain.home
    driver = selected_driver(root, original_home, args.gambuild_driver)
    driver_sha = digest(driver)
    cores = hardware_workers()
    output.mkdir()
    project, home = output / 'project', original_home
    bin_dir = output / 'bin'
    project.mkdir()
    bin_dir.mkdir()
    (output / 'package-home').mkdir()
    for name in ('gerbil', 'gxi', 'gxc'):
        (bin_dir / name).symlink_to(binary)
    for name in ('gsc', 'gsi'):
        (bin_dir / name).symlink_to(original_home / 'bin' / name)
    (bin_dir / 'gambuild-C').symlink_to(driver)
    for directory in ('list', 'encoding/json'):
        shutil.copytree(source / directory, project / directory)
    shutil.copy2(source / 'gerbil.pkg', project / 'gerbil.pkg')
    shutil.copy2(Path(__file__).with_name('stdlib_rebuild.ss'), project / 'build.ss')
    (project / 'build.ss').chmod(0o755)
    inputs = {str(p.relative_to(source)): digest(p) for directory in ('list', 'encoding/json')
              for p in (source / directory).glob('*.ss')}
    inputs['gerbil.pkg'] = digest(source / 'gerbil.pkg')
    binary_sha = digest(binary)
    env = toolchain.environment(build_environment(), package_home=output / 'package-home',
                                load_paths=[project / 'artifacts/lib', home / 'lib'],
                                workers=cores, bin_dir=bin_dir)
    report = dict(scope='original-stdlib-private-clean-build-test-not-MCP-admission',
                  qualified=False, performanceQualified=False, fullSuiteQualified=False,
                  productionAdmitted=False, hardwareWorkers=cores, sourceHashes=inputs,
                  binarySha256=binary_sha, gscSha256=digest(home / 'bin/gsc'), runs=[])
    report.update(gambuildDriver=str(driver.relative_to(root)),
                  gambuildDriverSha256=driver_sha)
    try:
        report['clean'] = execute([str(binary), 'clean'], project, env, output / 'clean.log',
                                  Limits('stdlib-clean', complete=30, first=None))
        if not report['clean']['passed']:
            return 1
        if list((project / 'artifacts').rglob('*.o*')):
            raise ValueError('native artifacts remain after clean')
        report['build'] = execute([str(binary), 'build'], project, env, output / 'build.log',
                                  Limits('stdlib-build', complete=50, first=5), compile_only=True)
        if not report['build']['passed']:
            return 1
        owners = ('list/list-test.ss', 'encoding/json/json-test.ss')
        test_started = time.monotonic()
        test_gate = ProgressiveGate(Limits('stdlib-test-wave', complete=112, first=5), test_started)
        test_shared = (test_gate, threading.Lock())

        def test(owner):
            row = execute([str(binary), 'test', '-v', '5', owner], project, env,
                          output / (owner.replace('/', '-') + '.log'),
                          Limits('stdlib-test', complete=112, first=5), shared=test_shared)
            lines = (output / (owner.replace('/', '-') + '.log')).read_text().splitlines()
            return qualify_test_result(row, owner, lines)

        with ThreadPoolExecutor(max_workers=cores) as pool:
            report['runs'] = list(pool.map(test, owners))
        report['testWaveWallSeconds'] = time.monotonic() - test_started
        report['testWaveFirstOutputSeconds'] = test_gate.first_event
        report['sourceUnchanged'] = all(digest(source / path) == sha and
            digest(project / path) == sha for path, sha in inputs.items())
        report['binaryUnchanged'] = digest(binary) == binary_sha
        report['driverUnchanged'] = digest(driver) == driver_sha
        report['qualified'] = report['sourceUnchanged'] and report['binaryUnchanged'] and report['driverUnchanged'] and all(
            row['passed'] for row in report['runs'])
        return 0 if report['qualified'] else 1
    finally:
        (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps({k: v for k, v in report.items() if k not in ('sourceHashes', 'runs')}), flush=True)


if __name__ == '__main__':
    raise SystemExit(main())
