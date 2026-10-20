"""Run bounded semantic controls; this never admits a performance candidate."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--binary', type=Path, required=True)
    parser.add_argument('--home', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument('--field-controls', action='store_true')
    selection.add_argument('--mark-fold-controls', action='store_true')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    binary, home, output = (path.resolve() for path in
                            (args.binary, args.home, args.output))
    for path in (binary, home, output):
        if not path.is_relative_to(root / '.data'):
            raise ValueError('isolated .data paths required')
    expected = json.loads((binary.parent / 'report.json').read_text())
    digest = hashlib.sha256(binary.read_bytes()).hexdigest()
    if not expected['qualified'] or digest != expected['binarySha256']:
        raise ValueError('native construction identity mismatch')
    controls = Path(__file__).with_name('mark-fold-native-controls.scm'
                                      if args.mark_fold_controls else
                                      'syntax-e-field-projection-controls.scm'
                                      if args.field_controls else
                                      'syntax-e-native-projection-controls.scm')
    env = dict(os.environ, GERBIL_HOME=str(home), GERBIL_LOADPATH=str(home / 'lib'))
    started = time.monotonic()
    child = subprocess.run([str(binary.parent / 'gxi'), '-e',
                            '(load ' + json.dumps(str(controls)) + ')'],
                           env=env, capture_output=True, text=True, timeout=20)
    lines = child.stdout.splitlines()
    cases = [line[8:] for line in lines if line.startswith('CASE-OK ')]
    count = 48 if args.mark_fold_controls else 26 if args.field_controls else 18
    passed = (child.returncode == 0 and len(cases) == len(set(cases)) == count
              and lines[-1:] == ['OK'] and not child.stderr)
    report = dict(semanticControlsPassed=passed, performanceAdmitted=False,
                  binarySha256=digest, exitCode=child.returncode,
                  controlsSha256=hashlib.sha256(controls.read_bytes()).hexdigest(),
                  wallSeconds=time.monotonic() - started, cases=cases,
                  stdout=child.stdout, stderr=child.stderr)
    with output.open('x') as stream:
        json.dump(report, stream, indent=2)
        stream.write('\n')
    print(json.dumps({key: report[key] for key in
                      ('semanticControlsPassed', 'exitCode', 'wallSeconds')}))
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
