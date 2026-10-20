"""Durable actual native semantics; not a complete test/performance admission."""
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
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    binary, output = args.binary.resolve(), args.output.resolve()
    if any(not path.is_relative_to(root / '.data') for path in (binary, output)):
        parser.error('isolated .data paths required')
    digest = hashlib.sha256(binary.read_bytes()).hexdigest()
    construction = json.loads((binary.parent / 'report.json').read_text())
    if not construction['qualified'] or construction['binarySha256'] != digest:
        raise ValueError('native construction identity mismatch')
    home = root / '.data/d1391-runtime-object-source/build'
    source = root / '.data/d1510-splice-cursor-source'
    env = dict(os.environ, GERBIL_HOME=str(home), GERBIL_LOADPATH=str(home / 'lib'),
               SPLICE_CURSOR_REFERENCE=str(source / 'reference.scm'),
               SPLICE_CURSOR_OVERLAY=str(source / 'restore-native.scm'))
    controls = Path(__file__).with_name('splice_cursor_controls.scm')
    started = time.monotonic()
    child = subprocess.run([str(binary.parent / 'gxi'), '-e',
                            '(load ' + json.dumps(str(controls)) + ')'],
                           env=env, capture_output=True, text=True, timeout=20)
    lines = child.stdout.splitlines()
    cases = [line[8:] for line in lines if line.startswith('CASE-OK ')]
    passed = (child.returncode == 0 and len(cases) == len(set(cases)) == 68 and
              lines[-1:] == ['OK'] and not child.stderr)
    report = dict(semanticControlsPassed=passed, performanceAdmitted=False,
                  binarySha256=digest, controlsSha256=hashlib.sha256(controls.read_bytes()).hexdigest(),
                  wallSeconds=time.monotonic() - started, exitCode=child.returncode,
                  cases=cases, stdout=child.stdout, stderr=child.stderr)
    with output.open('x') as stream:
        json.dump(report, stream, indent=2)
        stream.write('\n')
    print(json.dumps({key: report[key] for key in
                      ('semanticControlsPassed', 'wallSeconds', 'exitCode')}))
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
