"""Original and candidate Gambit process semantics, without package changes."""
import argparse
from collections import Counter
import json
from pathlib import Path

from bazel_host_environment import build_environment
from experiment_framework.context import data_path, retained_47, hardware_workers
from experiment_framework.process import execute
from native_object_manifest import digest
from progressive_performance_gate import Limits


EXPECTED_CASES = ('absolute-path-unchanged', 'child-path', 'empty-path-child-cwd',
                  'relative-path-child-cwd', 'trailing-empty-path', 'missing-path-default',
                  'no-shebang-shell-fallback', 'child-env-value', 'stderr-redirection',
                  'EACCES-search-continues', 'ENOTDIR-search-continues', 'missing-command',
                  'empty-command')
HASH_CASES = ('missing', 'insert-status', 'identity', 'replace-false', 'ref-rehash',
              'set-rehash', 'live-value', 'raw-slot-update', 'post-gc', 'resize-status',
              'collision-contents', 'dense-rehash', 'weak-insert', 'weak-live-roots')
CLOSEFROM_CASES = ('ordinary-descriptors-closed', 'ordinary-parent-descriptors-live',
                  'sparse-high-descriptors-closed', 'sparse-parent-descriptors-live',
                  'inventory-overflow-fallback-closes-all', 'overflow-parent-descriptors-live')
INTERN_CASES = ('empty', 'ascii', 'unicode', 'embedded-nul', 'long-and-tail-difference',
               'mutable-input', 'keyword-identity', 'table-growth-and-gc')
COPY_CASES = ('shared-pair', 'cyclic-pair', 'two-word-vector', 'two-word-string',
              'other-size-fallback', 'closure-roots', 'continuation-roots',
              'weak-live-roots', 'repeated-copy-stress')


def semantic_admission(text, passed, unchanged, contract='child-path'):
    if contract not in ('child-path', 'hash-cold-tail', 'closefrom', 'intern-string', 'two-word-copy'):
        raise ValueError('known semantic contract required')
    lines = text.splitlines()
    actual = [line[len('CASE-OK '):] for line in lines if line.startswith('CASE-OK ')]
    expected = {'child-path': EXPECTED_CASES, 'hash-cold-tail': HASH_CASES,
                'closefrom': CLOSEFROM_CASES, 'intern-string': INTERN_CASES,
                'two-word-copy': COPY_CASES}[contract]
    marker = {'child-path': 'child-path-spawn', 'hash-cold-tail': 'hash-cold-tail',
              'closefrom': 'closefrom', 'intern-string': 'intern-string',
              'two-word-copy': 'two-word-copy'}[contract]
    return (passed and unchanged and Counter(actual) == Counter(expected)
            and lines[-1:] == ['OK ' + marker + '-semantics']
            and '*** ERROR' not in text)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binary', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--contract', choices=('child-path', 'hash-cold-tail', 'closefrom', 'intern-string', 'two-word-copy'), default='child-path')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[4]
    output = data_path(root, args.output, fresh=True)
    baseline, candidate = retained_47(root), retained_47(root, args.binary.resolve())
    filename = {'child-path': 'child_path_spawn_semantics.ss',
                'hash-cold-tail': 'hash_cold_tail_semantics.ss',
                'closefrom': 'closefrom_semantics.ss',
                'intern-string': 'intern_string_compare_semantics.ss',
                'two-word-copy': 'two_word_copy_semantics.ss'}[args.contract]
    source = Path(__file__).resolve().parents[1] / filename
    source_sha = digest(source)
    output.mkdir()
    fixture = output / 'fixture'
    fixture.mkdir()
    (fixture / 'blocked').mkdir()
    (fixture / 'selected').write_text('#!/bin/sh\nprintf CHILD\n')
    (fixture / 'selected').chmod(0o700)
    (fixture / 'no-shebang').write_text('printf SCRIPT; exit 13\n')
    (fixture / 'no-shebang').chmod(0o700)
    (fixture / 'blocked/selected').write_text('not executable\n')
    workers, base = hardware_workers(), build_environment()
    report = dict(scope='generic-original-and-candidate-process-semantics', qualified=False,
                  performanceQualified=False, productionAdmitted=False, physicalCores=workers,
                  testSourceSha256=source_sha, runs=[])
    if args.contract == 'hash-cold-tail':
        report['scope'] = 'generic-original-and-candidate-gc-hash-semantics'
    elif args.contract == 'closefrom':
        report['scope'] = 'generic-original-and-candidate-descriptor-cleanup-semantics'
    elif args.contract == 'intern-string':
        report['scope'] = 'generic-original-and-candidate-string-intern-semantics'
    elif args.contract == 'two-word-copy':
        report['scope'] = 'generic-original-and-candidate-gc-copy-semantics'
    try:
        for role, tools in [('control', baseline), ('candidate', candidate)]:
            env = tools.environment(base, package_home=output / 'package',
                                    load_paths=[tools.home / 'lib'], workers=workers)
            env.update(GB_SPAWN_FIXTURE=str(fixture), PATH='/usr/bin:/bin')
            row = execute([str(tools.binary), '-e', source.read_text()], root, env, output / (role + '.log'),
                          Limits('process-semantics-' + role, first=5, complete=52, silence=None))
            text = (output / (role + '.log')).read_text(errors='replace')
            row.update(role=role, binarySha256=digest(tools.binary),
                       caseCount=sum(line.startswith('CASE-OK ') for line in text.splitlines()))
            row['command'] = [tools.binary.name, '-e', '<source-sha256:' + source_sha + '>']
            row['passed'] = semantic_admission(text, row['passed'], digest(source) == source_sha, args.contract)
            report['runs'].append(row)
            if not row['passed']:
                return 1
        report['qualified'] = True
        return 0
    finally:
        (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps(report), flush=True)
