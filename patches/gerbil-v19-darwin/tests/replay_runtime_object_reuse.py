#!/usr/bin/env python3
"""Replay the frozen object-reuse source profile without building or installing."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-cache', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    patch_dir = root / 'patches/gerbil-v19-darwin'
    profile = json.loads((patch_dir / 'runtime-object-reuse.json').read_text())
    output = args.output.resolve()
    if not output.is_relative_to(root / '.data'):
        parser.error('output must be a fresh directory inside project .data')
    # Verify every frozen input before creating the checkout.
    for entry in profile['patches']:
        patch = patch_dir / entry['file']
        if hashlib.sha256(patch.read_bytes()).hexdigest() != entry['sha256']:
            parser.error(f"patch identity changed: {entry['file']}")
    output.mkdir(parents=True, exist_ok=False)
    source = output / 'source'
    report = dict(profile=profile['profile'], sourceReplayPassed=False,
                  performanceQualified=False, releaseQualified=False, steps=[])

    def run(name, command, cwd=root):
        print(f'START {name}', flush=True)
        result = subprocess.run(command, cwd=cwd, capture_output=True, text=True, timeout=60)
        (output / f'{name}.log').write_text(result.stdout + result.stderr)
        report['steps'].append(dict(name=name, exitCode=result.returncode))
        result.check_returncode()
        print(f'OK {name}', flush=True)
        return result.stdout.strip()

    try:
        run('clone', ['git', 'clone', '--no-hardlinks', '--no-checkout',
                      str(args.source_cache.resolve()), str(source)])
        run('pin', ['git', 'checkout', '--detach', profile['gerbilRevision']], source)
        report['gerbilRevision'] = run('identity', ['git', 'rev-parse', 'HEAD'], source)
        gitlink = run('gambit-gitlink', ['git', 'ls-tree', 'HEAD', 'src/gambit'], source)
        if gitlink.split()[2] != profile['gambitRevision']:
            raise RuntimeError('Gambit gitlink does not match the frozen profile')
        for entry in profile['patches']:
            patch = str(patch_dir / entry['file'])
            run(f"check-{entry['file'][:4]}", ['git', 'apply', '--check', patch], source)
            run(f"apply-{entry['file'][:4]}", ['git', 'apply', patch], source)
        run('whitespace', ['git', 'diff', '--check'], source)
        files = run('changed-files', ['git', 'diff', '--name-only'], source).splitlines()
        expected = ['src/gerbil/compiler/base.ss', 'src/gerbil/compiler/driver.ss', 'src/std/make.ss']
        if sorted(files) != expected:
            raise RuntimeError('source replay changed unexpected files')
        report['changedFiles'] = files
        report['patches'] = profile['patches']
        report['sourceReplayPassed'] = True
    finally:
        (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    main()
