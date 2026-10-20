"""Matched interpreter entry diagnostics; not package performance admission."""
import argparse
import json
import os
from pathlib import Path
import statistics
import time

from experiment_framework.context import data_path, retained_47
from experiment_framework.process import record
from native_object_manifest import digest


MARKER = 'ENTRY-STARTUP-OK'
KNOWN_WARNING = '*** WARNING module std/net/request is DEPRECATED and will be removed in the future'


def commands(bin_dir):
    expression = f'(displayln "{MARKER}")'
    args = ['-e', expression]
    return {
        'gxi-direct': [str(bin_dir / 'gxi'), *args],
        'gxpkg-env-absolute': [str(bin_dir / 'gxpkg'), 'env', str(bin_dir / 'gxi'), *args],
        'gerbil-env-absolute': [str(bin_dir / 'gerbil'), 'env', str(bin_dir / 'gxi'), *args],
        'gerbil-env-path': [str(bin_dir / 'gerbil'), 'env', 'gxi', *args],
    }


def passed(exit_code, log):
    return exit_code == 0 and payload(log) == [MARKER]


def payload(log):
    return [line for line in log.splitlines() if line != KNOWN_WARNING]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--rounds', type=int, choices=range(1, 6), default=2)
    parser.add_argument('--project', type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[4]
    output = data_path(root, args.output, fresh=True)
    toolchain = retained_47(root)
    project = data_path(root, args.project) if args.project else None
    if project and not (project / 'gerbil.pkg').is_file():
        parser.error('a real package checkout with gerbil.pkg is required')
    package_digest = digest(project / 'gerbil.pkg') if project else None
    output.mkdir(parents=True)
    bin_dir = output / 'bin'
    bin_dir.mkdir()
    for tool in ('gerbil', 'gxi', 'gxpkg'):
        (bin_dir / tool).symlink_to(toolchain.binary)
    (bin_dir / 'gsc').symlink_to(toolchain.home / 'bin/gsc')
    package_home = project / '.gerbil' if project else output / 'packages'
    if not project:
        package_home.mkdir()
    env = toolchain.environment(os.environ, package_home=package_home,
                                load_paths=[], workers=1, bin_dir=bin_dir)
    for name in ('GERBIL_PREFIX', 'GERBIL_BUILD_RELEASE', 'GERBIL_BUILD_OPTIMIZED'):
        env.pop(name, None)
    cwd = project or output
    package_env = dict(env)
    if project:
        package_env.pop('GERBIL_PATH', None)
    report = dict(schema=1, diagnosticOnly=True, productionAdmitted=False,
                  performanceQualified=False, completed=False,
                  scope='retained dynamic tool aliases; no native gxpkg A/B',
                  binarySha256=digest(toolchain.binary), rows=[])
    if project:
        report.update(project=str(project.relative_to(root)), packageManifestSha256=package_digest,
                      packageContextAutoDetected=True)
    try:
        selection_log = output / 'path-selection.log'
        shell = ('test "$GERBIL_PATH" = "$1" && test "$PWD" = "$2" && command -v gxi')
        code = record([str(bin_dir / 'gerbil'), 'env', '/bin/sh', '-c', shell,
                       'entry-probe', str(package_home), str(cwd)],
                      cwd, package_env, selection_log, timeout=15)
        selected = payload(selection_log.read_text())
        report['pathSelectsExpectedGxi'] = code == 0 and selected == [str(bin_dir / 'gxi')]
        if not report['pathSelectsExpectedGxi']:
            raise ValueError('package environment selected a different gxi')
        entries = commands(bin_dir)
        for index in range(args.rounds):
            order = list(entries) if index % 2 == 0 else list(reversed(entries))
            for name in order:
                log = output / f'{index + 1}-{name}.log'
                start = time.monotonic()
                code = record(entries[name], cwd,
                              env if name == 'gxi-direct' else package_env,
                              log, timeout=15)
                elapsed = time.monotonic() - start
                content = log.read_text()
                ok = passed(code, content)
                report['rows'].append(dict(round=index + 1, entry=name,
                                           seconds=elapsed, exitCode=code, passed=ok,
                                           knownDeprecationWarnings=content.splitlines().count(KNOWN_WARNING)))
                print(f'{index + 1} {name}: {elapsed:.3f}s passed={ok}', flush=True)
                if not ok:
                    raise ValueError('entry did not produce the exact final marker')
        report['medianSeconds'] = {
            name: statistics.median(row['seconds'] for row in report['rows']
                                    if row['entry'] == name) for name in entries}
        report['inputUnchanged'] = digest(toolchain.binary) == report['binarySha256']
        if project:
            report['packageManifestUnchanged'] = digest(project / 'gerbil.pkg') == package_digest
            report['inputUnchanged'] &= report['packageManifestUnchanged']
        report['completed'] = report['inputUnchanged']
        return 0 if report['completed'] else 1
    finally:
        (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    raise SystemExit(main())
