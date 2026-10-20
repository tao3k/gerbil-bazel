"""Compile one private RTS archive member with a byte-identical control."""
import argparse
import hashlib
import json
from pathlib import Path
import shlex
import shutil
import subprocess

from bazel_host_environment import build_environment
from experiment_framework.context import data_path
from experiment_framework.process import record
from native_object_manifest import digest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--candidate', choices=('child-path', 'hash-cold-tail', 'darwin-closefrom', 'intern-string', 'two-word-copy', 'gc-mark-probe', 'allocation-sites'), default='child-path')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[4]
    source = data_path(root, args.source)
    archive = data_path(root, args.archive)
    output = data_path(root, args.output, fresh=True)
    filename = {'child-path': 'os_io.c', 'hash-cold-tail': 'mem.c',
                'darwin-closefrom': 'os_setup.c', 'intern-string': 'mem.c',
                'two-word-copy': 'mem.c', 'gc-mark-probe': 'mem.c',
                'allocation-sites': '_thread.c'}[args.candidate]
    member = Path(filename).with_suffix('.o').name
    if source.name != filename:
        raise ValueError('one original ' + filename + ' archive member required')
    if args.candidate == 'child-path':
        from gambit_child_path_spawn import transform
    elif args.candidate == 'hash-cold-tail':
        from gambit_hash_cold_tail import transform
    elif args.candidate == 'darwin-closefrom':
        from gambit_darwin_closefrom import transform
    elif args.candidate == 'intern-string':
        from gambit_intern_string_compare import transform
    elif args.candidate == 'gc-mark-probe':
        from prepare_gc_mark_probe import inject as transform
    elif args.candidate == 'allocation-sites':
        from gambit_allocation_sites import instrument as transform
    else:
        from gambit_two_word_copy import transform
    env = build_environment()
    command = shlex.split(subprocess.check_output(
        ['make', '-n', '-W', filename, member], cwd=source.parent, env=env, text=True).strip())
    if command[0] != env['CC'] or command.count(filename) != 1:
        raise ValueError('original GNU RTS compiler command required')
    expected = hashlib.sha256(subprocess.check_output(
        ['ar', '-p', str(archive), member], env=env)).hexdigest()
    inputs = {str(p.relative_to(root)): digest(p) for p in
              [source, archive, source.parent / 'makefile']}
    output.mkdir()
    report = dict(scope='private-child-path-runtime-io-not-performance-admission',
                  performanceQualified=False, productionAdmitted=False, completed=False,
                  inputHashes=inputs, expectedOriginalMember=expected, steps=[])
    report['candidate'] = args.candidate
    if args.candidate == 'hash-cold-tail':
        report['scope'] = 'private-hash-cold-tail-rts-not-performance-admission'
    elif args.candidate == 'darwin-closefrom':
        report['scope'] = 'private-darwin-closefrom-rts-not-performance-admission'
    elif args.candidate == 'intern-string':
        report['scope'] = 'private-intern-string-rts-not-performance-admission'
    elif args.candidate == 'two-word-copy':
        report['scope'] = 'private-two-word-copy-rts-not-performance-admission'
    elif args.candidate == 'gc-mark-probe':
        report.update(scope='private-gc-mark-census-not-performance-admission',
                      diagnosticOnly=True)
    elif args.candidate == 'allocation-sites':
        report.update(scope='original-thread-physical-allocation-census-not-performance',
                      diagnosticOnly=True)
    try:
        for role in ('control', 'candidate'):
            selected = source
            if role == 'candidate':
                selected = output / filename
                selected.write_text(transform(source.read_text()))
            obj = output / (member if role == 'candidate' else 'control.o')
            compile_command = list(command)
            compile_command[compile_command.index(filename)] = str(selected)
            compile_command[compile_command.index('-o') + 1] = str(obj)
            code = record(compile_command, source.parent, env, output / (role + '.log'), timeout=120)
            report['steps'].append(dict(role=role, exitCode=code))
            if code:
                return 1
            if role == 'control':
                report['controlMatchesOriginalMember'] = digest(obj) == expected
                if not report['controlMatchesOriginalMember']:
                    return 1
        replacement = output / 'diagnostic.a'
        shutil.copyfile(archive, replacement)
        for name, cmd in [('replace', ['ar', 'r', str(replacement), str(output / member)]),
                          ('index', ['ranlib', str(replacement)])]:
            code = record(cmd, root, env, output / (name + '.log'), timeout=15)
            if code:
                return 1
        original_members = subprocess.check_output(['ar', '-t', str(archive)], text=True).splitlines()
        candidate_members = subprocess.check_output(['ar', '-t', str(replacement)], text=True).splitlines()
        if original_members != candidate_members:
            raise ValueError('archive member inventory changed')
        report['preservedArchiveMembers'] = {}
        for name in original_members:
            if name == member or name.startswith('__.SYMDEF'):
                continue
            old = subprocess.check_output(['ar', '-p', str(archive), name])
            new = subprocess.check_output(['ar', '-p', str(replacement), name])
            if old != new:
                raise ValueError('unowned archive member changed: ' + name)
            report['preservedArchiveMembers'][name] = hashlib.sha256(old).hexdigest()
        report['inputsUnchanged'] = all(digest(root / p) == sha for p, sha in inputs.items())
        report['artifacts'] = {p.name: digest(p) for p in output.iterdir() if p.is_file()}
        report['completed'] = report['inputsUnchanged']
        return 0 if report['completed'] else 1
    finally:
        (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps({k: v for k, v in report.items() if k != 'inputHashes'}), flush=True)
