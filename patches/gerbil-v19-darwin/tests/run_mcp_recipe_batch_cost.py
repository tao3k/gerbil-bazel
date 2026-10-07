"""Attribute original five-recipe expressions; this is not suite admission."""
import argparse
from collections import Counter
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import time

from bazel_host_environment import build_environment
from progressive_performance_gate import force_stop


def outcomes(text):
    result = []
    for line in text.splitlines():
        for kind in ('PASS', 'FAIL'):
            prefix = 'GERBIL-MCP-VERIFY-' + kind + ':'
            if line.startswith(prefix):
                result.append((kind, line[len(prefix):].split('\t', 1)[0]))
    return Counter(result)


def phases(text):
    rows = []
    for line in text.splitlines():
        if not line.startswith('BATCH-PHASE\t'):
            continue
        fields = line.split('\t')
        if len(fields) != 23:
            raise ValueError('phase, wall and twenty statistics required')
        numbers = [float(value) for value in fields[2:]]
        if not all(math.isfinite(value) for value in numbers):
            raise ValueError('finite statistics required')
        rows.append(dict(phase=fields[1], wall=numbers[0], stats=numbers[1:]))
    if [row.get('phase') for row in rows] != ['start', 'imports', 'checks']:
        raise ValueError('three ordered real phase completions required')
    if any(len(row.get('stats', [])) != 20 for row in rows):
        raise ValueError('actual Gambit process-statistics layout required')
    return rows


def phase_expression(name):
    # These observations complete real CLI/import/check phases, not heartbeats.
    return ('(begin (display "BATCH-PHASE\\t' + name + '\\t") '
            '(write (time->seconds (current-time))) '
            '(for-each (lambda (x) (display "\\t") (write x)) '
            '(f64vector->list (##process-statistics))) (newline))')


def batch_control_matches(code, text, observed_code, observed_text, ids):
    if code != observed_code or outcomes(text) != outcomes(observed_text):
        return False
    if code == 0:
        return Counter(key[1] for key in outcomes(text).elements()) == Counter(ids)
    return (code == 70 and 'cannot find library module' in text and
            'cannot find library module' in observed_text)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--reader-attribution', action='store_true')
    parser.add_argument('--native-sample', action='store_true')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    out = args.output.resolve()
    if not out.is_relative_to(root / '.data') or out.exists():
        parser.error('fresh persistent .data output required')
    if args.native_sample and args.reader_attribution:
        parser.error('use one independent attribution method per diagnostic')
    binary = root / '.data/d1510-reader-whitespace-native-v2/gerbil'
    home = root / '.data/d1510-mcp-test-source-home-v2/build'
    project = root / '.data/d1510-reader-whitespace-progressive-v1/0-candidate/project'
    driver = root / '.data/d1510-shell-substitution/bin'
    expected = '1f83878a01744817ceb6e74e5d07138948930a41386e568d156210ce9108bb21'
    if hashlib.sha256(binary.read_bytes()).hexdigest() != expected:
        raise ValueError('frozen host changed')
    sources = ['util/verify.ss', 'util/cookbook.ss', 'data/cookbooks.json',
               'data/builtin-recipes.json']
    before = {name: hashlib.sha256((project / name).read_bytes()).hexdigest()
              for name in sources}
    out.mkdir()
    gxi = out / 'gxi'
    gxi.symlink_to(binary)
    env = build_environment()
    for key in tuple(env):
        if key.startswith('GAMBIT_DARWIN_') or key == 'GERBIL_BUILD_PREFIX':
            env.pop(key)
    env.update(GERBIL_HOME=str(home), GERBIL_PATH=str(project / '.gerbil'),
               GERBIL_LOADPATH=f'{project / ".gerbil/lib"}:{home / "lib"}:{project}',
               GAMBOPT=f'~~bin={driver},~~lib={home / "lib"},~~include={home / "include"}')
    report = dict(scope='three-original-five-recipe-batch-phase-controls',
                  fullSuiteQualified=False, performanceQualified=False,
                  binarySha256=expected, sourceSha256=before, runs=[])
    report['nativeSampling'] = args.native_sample

    def execute(name, expressions=None, source=None):
        command = [str(gxi)]
        if source:
            command.append(str(source))
        for expression in expressions or []:
            command.extend(['-e', expression])
        started = time.monotonic()
        with (out / (name + '.log')).open('wb') as log:
            process = subprocess.Popen(command, cwd=project, env=env, stdout=log,
                                       stderr=subprocess.STDOUT, start_new_session=True)
            sampler = None
            sample_log = None
            try:
                if args.native_sample and name.endswith('-observed'):
                    sample_log = (out / (name + '-sampler.log')).open('wb')
                    sampler = subprocess.Popen(['/usr/bin/sample', str(process.pid), '1', '1',
                                                '-file', str(out / (name + '.sample.txt'))],
                                               stdout=sample_log, stderr=subprocess.STDOUT,
                                               start_new_session=True)
                code = process.wait(timeout=30)
                if sampler is not None:
                    report.setdefault('samples', []).append(dict(name=name,
                        exitCode=sampler.wait(timeout=10),
                        captured=(out / (name + '.sample.txt')).exists()))
            finally:
                if process.poll() is None:
                    force_stop(process)
                if sampler is not None and sampler.poll() is None:
                    force_stop(sampler)
                if sample_log is not None:
                    sample_log.close()
        return code, time.monotonic() - started, (out / (name + '.log')).read_text()

    try:
        code, _, text = execute('expressions', source=Path(__file__).with_name(
            'mcp_recipe_batch_expressions.ss'))
        if code:
            raise ValueError('original recipe expression export failed')
        exported = json.loads(text)
        if exported['batchSize'] != 5 or len(exported['batches']) != 3:
            raise ValueError('original batch size or selected inventory changed')
        report['recipeCount'] = exported['recipeCount']
        for batch in exported['batches']:
            index = batch['index']
            original = [batch['imports'], batch['checks']]
            code, wall, text = execute(f'{index}-control', expressions=original)
            observed = [phase_expression('start'), original[0], phase_expression('imports'),
                        original[1], phase_expression('checks')]
            if args.reader_attribution:
                fixture = Path(__file__).with_name('mcp_recipe_module_read_probe.ss')
                observed.insert(0, '(load ' + json.dumps(str(fixture)) + ')')
                observed.append('(emit-module-read-probe!)')
            ocode, owall, otext = execute(f'{index}-observed', expressions=observed)
            actual = outcomes(text)
            same = batch_control_matches(code, text, ocode, otext, batch['ids'])
            row = dict(index=index, ids=batch['ids'], exactOutcomesMatch=same,
                       controlExitCode=code, observedExitCode=ocode,
                       recipeOutcomesComplete=(Counter(key[1] for key in actual.elements())
                                               == Counter(batch['ids'])),
                       controlWallSeconds=wall, observedWallSeconds=owall)
            if code or ocode:
                row['importAborted'] = True
                report['runs'].append(row)
                continue
            rows = phases(otext)
            row.update(importSeconds=rows[1]['wall'] - rows[0]['wall'],
                       checkSeconds=rows[2]['wall'] - rows[1]['wall'], phases=rows)
            if args.reader_attribution:
                reads = [line.split('\t', 3) for line in otext.splitlines()
                         if line.startswith('MODULE-READ\t')]
                row['moduleReadCalls'] = len(reads)
                row['moduleReadInclusiveSeconds'] = sum(float(fields[1]) for fields in reads)
                row['moduleReadInclusiveAllocatedBytes'] = sum(float(fields[2]) for fields in reads)
                row['readerAttributionObserved'] = bool(reads)
            report['runs'].append(row)
        report['sourceUnchanged'] = all(hashlib.sha256((project / name).read_bytes()).hexdigest()
                                        == digest for name, digest in before.items())
        report['semanticControlPassed'] = report['sourceUnchanged'] and all(
            row['exactOutcomesMatch'] for row in report['runs'])
        if args.reader_attribution:
            report['readerAttributionQualified'] = report['semanticControlPassed'] and all(
                row.get('readerAttributionObserved', False) for row in report['runs']
                if row['controlExitCode'] == 0)
    except Exception as error:
        report['failure'] = repr(error)
        report['semanticControlPassed'] = False
    (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({key: value for key, value in report.items() if key != 'runs'}))
    for row in report['runs']:
        print(json.dumps({key: value for key, value in row.items() if key != 'phases'}))
    passed = report['semanticControlPassed']
    if args.reader_attribution:
        passed = passed and report.get('readerAttributionQualified', False)
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
