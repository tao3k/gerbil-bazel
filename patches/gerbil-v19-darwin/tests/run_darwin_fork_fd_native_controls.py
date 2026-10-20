"""Actual Gambit child environment/ENOEXEC controls, not build/test admission."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import selectors
import subprocess
import time

from bazel_host_environment import build_environment
from progressive_performance_gate import GateViolation, Limits, ProgressiveGate, force_stop
from verify_reader_batch_50_baseline import main as verify


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--binary', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    out, candidate = args.output.resolve(), args.binary.resolve()
    if any(not p.is_relative_to(root / '.data') for p in (out, candidate)) or out.exists():
        parser.error('isolated candidate and fresh output required')
    verify()
    construction = json.loads((candidate.parent / 'report.json').read_text())
    if not construction['qualified'] or hashlib.sha256(candidate.read_bytes()).hexdigest() != construction['binarySha256']:
        raise ValueError('candidate provenance mismatch')
    out.mkdir()
    fixtures = out / 'fixtures'
    fixtures.mkdir()
    script = fixtures / 'no-shebang'
    script.write_text('printf SCRIPT-OK; exit 13\n')
    script.chmod(0o755)
    home = root / '.data/d1391-runtime-object-source/build'
    env = build_environment()
    env.update(GERBIL_HOME=str(home), GERBIL_LOADPATH=str(home / 'lib'),
               PATH=f'{fixtures}:/usr/bin:/bin')
    expression = '''
(let ((environment (map (lambda (kv) (string-append (car kv) "=" (cdr kv)))
                        (get-environment-variables))))
  (for-each
    (lambda (settings)
      (with-catch
        (lambda (e) (write (list 'error (no-such-file-or-directory-exception? e))) (newline) (force-output))
        (lambda ()
          (let* ((p (open-process settings)) (output (read-line p #f)) (status (process-status p)))
            (close-port p)
            (write (list 'child output status)) (newline) (force-output)))))
    (list
      (list path: "sh" arguments: (list "-c" "printf CHILD-OK; exit 7")
            environment: environment stdin-redirection: #t stdout-redirection: #t)
      (list path: "no-shebang" environment: environment stdin-redirection: #t stdout-redirection: #t)
      (list path: "no-shebang" environment: (list FIXTURE_PATH) stdin-redirection: #t stdout-redirection: #t)
      (list path: "definitely-missing-d1510" environment: environment stdin-redirection: #t stdout-redirection: #t))))
(displayln "CONTROLS-OK") (force-output)
'''.replace('FIXTURE_PATH', json.dumps('PATH=' + str(fixtures)))
    expected = ['(child "CHILD-OK" 1792)', '(child "SCRIPT-OK" 3328)',
                '(child "SCRIPT-OK" 3328)', '(error #t)', 'CONTROLS-OK']
    rows = []
    for role, binary in (('frozen', root / '.data/d1510-reader-batch-native-v1/gerbil'), ('candidate', candidate)):
        started = time.monotonic()
        gate = ProgressiveGate(Limits('actual-process-controls', complete=50, first=5, silence=5), started)
        process = subprocess.Popen([str(binary), '-e', expression], env=env, stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT, start_new_session=True)
        selector = selectors.DefaultSelector()
        selector.register(process.stdout, selectors.EVENT_READ)
        data = bytearray()
        row = dict(role=role, passed=False, binarySha256=hashlib.sha256(binary.read_bytes()).hexdigest())
        try:
            while selector.get_map() or process.poll() is None:
                gate.check(time.monotonic())
                for key, _ in selector.select(.025):
                    chunk = os.read(key.fileobj.fileno(), 65536)
                    if not chunk:
                        selector.unregister(key.fileobj)
                        continue
                    now = time.monotonic()
                    gate.output(now)
                    gate.first(now)
                    data.extend(chunk)
            gate.check(time.monotonic())
            row['exitCode'] = process.wait(timeout=1)
            row['lines'] = data.decode(errors='replace').splitlines()
            row['passed'] = row['exitCode'] == 0 and row['lines'] == expected
        except Exception as error:
            row['failure'] = repr(error)
            if isinstance(error, GateViolation):
                row['performanceStop'] = error.record
        finally:
            selector.close()
            if process.poll() is None:
                row['cleanup'] = force_stop(process)
            row['wallSeconds'] = time.monotonic() - started
            (out / (role + '.log')).write_bytes(data)
        rows.append(row)
    report = dict(controlsQualified=all(row['passed'] for row in rows), performanceAdmitted=False,
                  testQualified=False, productionAdmitted=False, runs=rows)
    (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))
    return 0 if report['controlsQualified'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
