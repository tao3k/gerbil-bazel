"""Record hardware-counter availability on the retained stdlib import path."""
import argparse
import json
import math
from pathlib import Path
import subprocess
import time
import xml.etree.ElementTree as ET

from bazel_host_environment import build_environment
from native_object_manifest import digest
from experiment_framework.context import data_path, hardware_workers, retained_47
from experiment_framework.process import record


def remaining_budget(started, budget):
    remaining = budget - (time.monotonic() - started)
    if remaining <= 0:
        raise TimeoutError('whole diagnostic budget exhausted')
    return remaining


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--template', choices=('CPU Counters', 'CPU Profiler'),
                        default='CPU Counters')
    parser.add_argument('--budget-seconds', type=float, default=150)
    args = parser.parse_args()
    if not math.isfinite(args.budget_seconds) or args.budget_seconds <= 0:
        parser.error('positive finite diagnostic budget required')
    root = Path(__file__).resolve().parents[3]
    output = data_path(root, args.output, fresh=True)
    toolchain = retained_47(root)
    binary, home, expected = toolchain.binary, toolchain.home, toolchain.expected_sha256
    workers = hardware_workers()
    env = toolchain.environment(build_environment(), package_home=output / 'empty-package-home',
                                load_paths=[home / 'lib'], workers=workers)
    expression = '(begin (import :std/make :std/test :std/build-script) (displayln "OK"))'
    command = ['xcrun', 'xctrace', 'record', '--template', args.template,
               '--output', str(output / 'profile.trace'), '--time-limit', '20s',
               '--no-prompt', '--target-stdout', str(output / 'target.log')]
    for key in ('GERBIL_HOME', 'GERBIL_LOADPATH', 'GERBIL_PATH', 'GERBIL_BUILD_CORES',
                'GERBIL_GSC', 'GAMBOPT'):
        command.extend(['--env', f'{key}={env[key]}'])
    command.extend(['--launch', '--', str(binary), '-e', expression])
    output.mkdir()
    report = dict(scope='retained-stdlib-import-hardware-counter-diagnostic',
                  diagnosticOnly=True, performanceQualified=False,
                  fullSuiteQualified=False, productionAdmitted=False,
                  qualified=False, binarySha256=expected, hardwareWorkers=workers,
                  expression=expression, schemas=[], template=args.template,
                  diagnosticBudgetSeconds=args.budget_seconds)
    before = digest(home / 'bin/gsc')
    started = time.monotonic()
    try:
        report['profilerExitCode'] = record(
            command, root, env, output / 'profiler.log',
            timeout=min(90, remaining_budget(started, args.budget_seconds)),
            termination_grace=0)
        if report['profilerExitCode']:
            raise RuntimeError('hardware counter recording failed; see profiler.log')
        toc = subprocess.check_output(
            ['xcrun', 'xctrace', 'export', '--input', str(output / 'profile.trace'), '--toc'],
            env=env, timeout=min(60, remaining_budget(started, args.budget_seconds)))
        (output / 'toc.xml').write_bytes(toc)
        tree = ET.fromstring(toc)
        target = tree.find('./run/info/target/process')
        if target is None:
            raise ValueError('launched target identity absent')
        report['targetPid'] = int(target.get('pid'))
        report['targetExitStatus'] = target.get('return-exit-status')
        report['schemas'] = [dict(table.attrib) for table in tree.findall('./run/data/table')]
        report['targetCompleted'] = (
            report['targetExitStatus'] == '0'
            and (output / 'target.log').read_text().splitlines()[-1:] == ['OK'])
        report['qualified'] = report['targetCompleted']
        if args.template == 'CPU Profiler' and report['targetCompleted']:
            subprocess.run(
                ['xcrun', 'xctrace', 'export', '--input', str(output / 'profile.trace'),
                 '--xpath', '/trace-toc/run[@number="1"]/data/table[@schema="cpu-profile"]',
                 '--output', str(output / 'cpu-profile.xml')],
                env=env, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                timeout=remaining_budget(started, args.budget_seconds))
            report['cpuProfileExported'] = True
    except (ValueError, RuntimeError, subprocess.SubprocessError, OSError) as error:
        report['failure'] = str(error)
        report['qualified'] = False
    finally:
        report['binaryUnchanged'] = digest(binary) == expected
        report['gscUnchanged'] = digest(home / 'bin/gsc') == before
        report['qualified'] &= report['binaryUnchanged'] and report['gscUnchanged']
        report['recordingWallSecondsNotProductTiming'] = time.monotonic() - started
        (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps({key: report.get(key) for key in (
            'qualified', 'targetPid', 'targetExitStatus', 'failure',
            'binaryUnchanged', 'gscUnchanged', 'recordingWallSecondsNotProductTiming')}), flush=True)
    return 0 if report['qualified'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
