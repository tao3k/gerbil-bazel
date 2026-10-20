"""Bounded atomic control, not a complete MCP/build performance receipt."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time

from bazel_host_environment import build_environment
from progressive_performance_gate import force_stop


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--substring', action='store_true')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    out = args.output.resolve()
    if not out.is_relative_to(root / '.data') or out.exists():
        parser.error('fresh persistent .data output required')
    binary = root / '.data/d1510-reader-whitespace-native-v2/gerbil'
    home = root / '.data/d1510-mcp-test-source-home-v2/build'
    project = root / '.data/d1510-reader-whitespace-progressive-v1/0-candidate/project'
    expected = '1f83878a01744817ceb6e74e5d07138948930a41386e568d156210ce9108bb21'
    if hashlib.sha256(binary.read_bytes()).hexdigest() != expected:
        raise ValueError('frozen candidate changed')
    out.mkdir()
    (out / 'gxi').symlink_to(binary)
    text = out / 'strings.txt'
    with text.open('wb') as log:
        subprocess.run(['strings', '-n', '4', str(binary)], stdout=log, check=True, timeout=30)
    env = build_environment()
    env.update(GERBIL_HOME=str(home), GERBIL_PATH=str(project / '.gerbil'),
               GERBIL_LOADPATH=f'{project / ".gerbil/lib"}:{home / "lib"}:{project}',
               PREGEXP_ATOMIC_STRINGS=str(text))
    source = Path(__file__).with_name('read_substring_atomic.ss' if args.substring
                                    else 'pregexp_reuse_atomic.ss')
    started = time.monotonic()
    report = dict(scope=('atomic-four-MiB-capture-read-substring' if args.substring else
                         'atomic-ten-audit-patterns-first-2000-selected-binary-strings'),
                  fullSuiteQualified=False, binarySha256=expected,
                  fixtureSha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                  stringsSha256=hashlib.sha256(text.read_bytes()).hexdigest())
    with (out / 'atomic.log').open('wb') as log:
        process = subprocess.Popen([str(out / 'gxi'), str(source)], cwd=project,
                                   env=env, stdout=log, stderr=subprocess.STDOUT,
                                   start_new_session=True)
        try:
            report['exitCode'] = process.wait(timeout=60)
        except subprocess.TimeoutExpired:
            report['cleanup'] = force_stop(process)
            report['failure'] = 'atomic-60-second-execution-bound'
    lines = (out / 'atomic.log').read_text(errors='replace').splitlines()
    report['runs'] = [json.loads(line) for line in lines if line.startswith('{')]
    report['semanticControlPassed'] = (report.get('exitCode') == 0 and lines[-1:] == ['OK']
                                      and len(report['runs']) == 4 and
                                      all(row['exactPositionsMatch'] for row in report['runs']))
    report['wallSeconds'] = time.monotonic() - started
    (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))
    return 0 if report['semanticControlPassed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
