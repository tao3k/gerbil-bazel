"""Reached optimizer metadata costs; no cold-build or speedup admission."""
import argparse
import hashlib
import json
import math
from pathlib import Path

from bazel_host_environment import build_environment
from experiment_framework.context import data_path, hardware_workers, retained_47
from experiment_framework.process import record
from native_object_manifest import digest


def parse(text):
    calls, compile_cpu, code, pending = [], [], {}, []
    for line in text.splitlines():
        if line.startswith('METADATA-CALL\t'):
            fields = line.split('\t')
            if len(fields) not in (5, 6):
                raise ValueError('complete metadata interval required')
            depth, path, inclusive, own = fields[1:5]
            depth, inclusive, own = int(depth), float(inclusive), float(own)
            if depth < 0 or not all(math.isfinite(v) and v >= -0.001 for v in (inclusive, own)):
                raise ValueError('valid metadata CPU intervals required')
            if own > inclusive + 0.001:
                raise ValueError('own interval exceeds inclusive interval')
            children = []
            while pending and pending[-1]['depth'] > depth:
                child = pending.pop()
                if child['depth'] != depth + 1:
                    raise ValueError('complete metadata postorder required')
                children.append(child)
            if abs(own - (inclusive - sum(c['cpuInclusive'] for c in children))) > 0.001:
                raise ValueError('own CPU must subtract immediate children exactly once')
            calls.append(dict(depth=depth, path=path, cpuInclusive=inclusive, cpuOwn=own))
            if len(fields) == 6:
                calls[-1]['worker'] = fields[5]
            pending.append(calls[-1])
        elif line.startswith('METADATA-COMPILE-CPU\t'):
            compile_cpu.append(float(line.split('\t')[1]))
        elif line.startswith('METADATA-CODE\t'):
            _, suffix, forms = line.split('\t', 2)
            if suffix in code or not forms.startswith('('):
                raise ValueError('one structured code inventory per suffix required')
            code[suffix] = hashlib.sha256(forms.encode()).hexdigest()
    if (len(compile_cpu) != 1 or not math.isfinite(compile_cpu[0]) or compile_cpu[0] < 0
            or text.splitlines()[-1:] != ['OK metadata-compile']):
        raise ValueError('one completed compilation and final marker required')
    if sum(row['cpuOwn'] for row in calls) > compile_cpu[0] + 0.001:
        raise ValueError('observed own CPU exceeds enclosing compilation')
    if any(row['depth'] != 0 for row in pending):
        raise ValueError('completed metadata roots required')
    return dict(compileCpu=compile_cpu[0], calls=calls, timestampNormalizedCode=code,
                metadataOwnCpu=sum(row['cpuOwn'] for row in calls))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--workers', action='store_true', help='observe a real hardware-concurrent std/make build')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[4]
    output = data_path(root, args.output, fresh=True)
    tools = retained_47(root)
    probe = Path(__file__).resolve().parents[1] / 'compiler_metadata_probe.scm'
    inputs = {str(p.relative_to(root)): digest(p) for p in (tools.binary, probe)}
    output.mkdir()
    (output / 'probe.scm').write_text(probe.read_text())
    report = dict(scope='original-optimizer-metadata-observation-not-performance-admission',
                  qualified=False, performanceQualified=False, productionAdmitted=False,
                  inputHashes=inputs, runs=[])
    workers, base = hardware_workers(), build_environment()
    report['hardwareWorkers'] = workers
    try:
        if args.workers:
            fixture, dest = output / 'fixture', output / 'lib'
            fixture.mkdir()
            dest.mkdir()
            for i in range(workers):
                library = ':std/list/list' if i % 2 == 0 else ':std/encoding/json'
                source = fixture / ('m' + str(i) + '.ss')
                source.write_text('package: probe\n(import ' + library + ')\n'
                                  '(export value_m' + str(i) + ')\n'
                                  '(def (value_m' + str(i) + ' value) value)\n')
                inputs[str(source.relative_to(root))] = digest(source)
            env = tools.environment(base, package_home=output / 'package',
                                    load_paths=[dest, tools.home / 'lib'], workers=workers)
            env['GERBIL_GCC'] = env['CC']
            code = probe.read_text() + '\n(metadata-workers ' + json.dumps(str(fixture)) + ' ' + json.dumps(str(dest)) + ' ' + str(workers) + ')\n'
            log = output / 'workers.log'
            status = record([str(tools.binary), '-e', code], root, env, log, timeout=60)
            row = dict(role='workers-observed', exitCode=status)
            report['runs'].append(row)
            if status:
                return 1
            text = log.read_text()
            row.update(parse(text))
            expected = ['METADATA-CONSUMER-OK\t' + str(i) for i in range(workers)]
            actual = [line for line in text.splitlines() if line.startswith('METADATA-CONSUMER-OK\t')]
            if actual != expected or not row['calls']:
                raise ValueError('all compiled consumers must execute and metadata must be reached')
            row['consumerCases'] = len(actual)
            row['nativeImages'] = len(list(dest.rglob('*.o1')))
            if row['nativeImages'] < workers:
                raise ValueError('real native compiler outputs required')
            report['inputsUnchanged'] = all(digest(root / p) == sha for p, sha in inputs.items())
            report['qualified'] = report['inputsUnchanged']
            return 0 if report['qualified'] else 1
        for name, library in [('list', ':std/list/list'), ('json', ':std/encoding/json')]:
            source = output / (name + '.ss')
            source.write_text('(import ' + library + ')\n(export identity-value)\n'
                              '(def (identity-value value) value)\n')
            report['inputHashes'][str(source.relative_to(root))] = digest(source)
            for role in ('control', 'observed'):
                dest = output / (name + '-' + role)
                dest.mkdir()
                env = tools.environment(base, package_home=output / 'package',
                                        load_paths=[tools.home / 'lib'], workers=workers)
                code = probe.read_text() + '\n(metadata-compile ' + json.dumps(str(source)) + ' ' + json.dumps(str(dest)) + ' ' + ('#t' if role == 'observed' else '#f') + ')\n'
                log = output / (name + '-' + role + '.log')
                status = record([str(tools.binary), '-e', code], root, env, log, timeout=60)
                row = dict(library=library, role=role, exitCode=status)
                report['runs'].append(row)
                if status:
                    return 1
                row.update(parse(log.read_text()))
                row['artifacts'] = {str(p.relative_to(dest)): digest(p)
                                    for p in dest.rglob('*') if p.is_file()}
                if not row['artifacts']:
                    raise ValueError('real compiler outputs required')
            control, observed = report['runs'][-2:]
            raw_names = set(control['artifacts']) | set(observed['artifacts'])
            runtime_names = {name + '~0.scm', 'static/' + name + '.scm'}
            observed['artifactParity'] = (
                set(control['artifacts']) == set(observed['artifacts'])
                and all(control['artifacts'][p] == observed['artifacts'][p]
                        for p in raw_names - runtime_names)
                and control['timestampNormalizedCode'] == observed['timestampNormalizedCode']
                and bool(control['timestampNormalizedCode'])
                and all(role['artifacts'][name + '~0.scm'] == role['artifacts']['static/' + name + '.scm']
                        for role in (control, observed)))
            if not observed['artifactParity'] or not observed['calls']:
                return 1
        report['inputsUnchanged'] = all(digest(root / p) == sha for p, sha in inputs.items())
        report['qualified'] = report['inputsUnchanged']
        return 0 if report['qualified'] else 1
    finally:
        (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps(dict(qualified=report['qualified'], hardwareWorkers=workers,
                              runs=[{k: v for k, v in row.items() if k not in ('calls', 'artifacts')}
                                    for row in report['runs']])), flush=True)
