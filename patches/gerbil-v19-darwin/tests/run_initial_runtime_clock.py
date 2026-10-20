"""Locate startup intervals on an existing diagnostic host, not a speed test."""
import argparse
import json
import os
from pathlib import Path
import resource
import subprocess
import time

from probe_retained_native_loader import FROZEN, align_initial_interval, digest, parse_initial_stats, parse_stats
from progressive_performance_gate import force_stop


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    host, output = args.host.resolve(), args.output.resolve()
    if (os.uname().sysname != 'Darwin' or output.exists()
            or not all(path.is_relative_to(root / '.data') for path in (host, output))):
        parser.error('existing isolated Darwin diagnostic and fresh persistent output required')
    manifest = json.loads((host / 'report.json').read_text())
    probe = host / 'gxi'
    control = root / '.data/d1510-reader-whitespace-native-v2/gerbil'
    if (not manifest.get('qualified') or not manifest.get('initialSetupRequested')
            or not manifest.get('baselineUnchanged') or digest(control) != FROZEN
            or digest(probe) != manifest['diagnosticBinarySha256']):
        raise ValueError('exact completed initial-setup diagnostic required')
    output.mkdir()
    (output / 'package-home').mkdir()
    (output / 'control').mkdir()
    (output / 'control/gxi').symlink_to(control)
    home = root / '.data/d1510-mcp-test-source-home-v2/build'
    env = dict(os.environ)
    for key in tuple(env):
        if key.startswith(('GAMBIT_DARWIN_', 'GERBIL_MCP_', 'GB_LOADER_STATS', 'GB_INITIAL_SETUP_STATS')):
            env.pop(key)
    env.pop('GERBIL_BUILD_PREFIX', None)
    env.pop('GAMBOPT', None)
    env.update(GERBIL_HOME=str(home), GERBIL_PATH=str(output / 'package-home'),
               GERBIL_LOADPATH=str(home / 'lib'), GAMBIT_EMBEDDED_NATIVE='0')
    report = dict(qualified=False, performanceQualified=False, productionAdmitted=False,
                  scope='five-empty-startup-pairs-initial-boundary-not-build-or-test',
                  diagnosticSha256=manifest['diagnosticBinarySha256'], runs=[])
    try:
        for index in range(5):
            roles = ('control', 'probe') if index % 2 == 0 else ('probe', 'control')
            for role in roles:
                name = f'{index}-{role}'
                binary = output / 'control/gxi' if role == 'control' else probe
                local = dict(env, GB_INITIAL_SETUP_STATS=str(output / (name + '-initial')),
                             GB_LOADER_STATS=str(output / (name + '-loader')))
                log_path = output / (name + '.log')
                before = resource.getrusage(resource.RUSAGE_CHILDREN)
                with log_path.open('w') as log:
                    launched = time.clock_gettime_ns(time.CLOCK_MONOTONIC)
                    child = subprocess.Popen([str(binary), '-e', '(display "BOOT-OK\\n")'],
                        cwd=output, env=local, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
                    try:
                        child.wait(timeout=20)
                    finally:
                        if child.poll() is None:
                            force_stop(child)
                    finished = time.clock_gettime_ns(time.CLOCK_MONOTONIC)
                after = resource.getrusage(resource.RUSAGE_CHILDREN)
                row = dict(round=index, role=role, exitCode=child.returncode,
                           processSeconds=(finished-launched) / 1e9,
                           userCpuSeconds=after.ru_utime-before.ru_utime,
                           systemCpuSeconds=after.ru_stime-before.ru_stime)
                report['runs'].append(row)
                if child.returncode or log_path.read_text().splitlines() != ['BOOT-OK']:
                    raise ValueError('original empty-startup completion required')
                if role == 'probe':
                    initial_files = list(output.glob(name + '-initial.*.json'))
                    loader_files = list(output.glob(name + '-loader.*.json'))
                    if len(initial_files) != 1:
                        raise ValueError('exactly one process initial-setup receipt required')
                    row['initialSetup'] = align_initial_interval(
                        parse_initial_stats(json.loads(initial_files[0].read_text())),
                        dict(launchedNs=launched, finishedNs=finished))
                    row['loaderReceiptPresent'] = bool(loader_files)
                    if len(loader_files) > 1:
                        raise ValueError('unexpected child loader receipts')
                    if loader_files:
                        row['loader'] = parse_stats(json.loads(loader_files[0].read_text()))
                print(json.dumps(row), flush=True)
        report['binaryUnchanged'] = digest(control) == FROZEN and digest(probe) == manifest['diagnosticBinarySha256']
        report['qualified'] = len(report['runs']) == 10 and report['binaryUnchanged']
    except Exception as error:
        report['failure'] = repr(error)
    finally:
        (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    return 0 if report['qualified'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
