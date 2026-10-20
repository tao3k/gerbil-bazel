"""Compiled Scheme consumer A/B/B/A; not MCP cold-build or suite admission."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import selectors
import subprocess
import time

from bazel_host_environment import build_environment
from progressive_performance_gate import Limits, ProgressiveGate, force_stop
from verify_reader_batch_50_baseline import main as verify


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(command, env, log, phase):
    started = time.monotonic()
    gate = ProgressiveGate(Limits(phase, complete=50, first=5, silence=5), started)
    child = subprocess.Popen(command, env=env, stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, start_new_session=True)
    selector = selectors.DefaultSelector()
    selector.register(child.stdout, selectors.EVENT_READ)
    data = bytearray()
    row = dict(passed=False)
    try:
        while selector.get_map() or child.poll() is None:
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
        row.update(exitCode=child.wait(timeout=1), lines=data.decode(errors='replace').splitlines())
        row['passed'] = row['exitCode'] == 0
    except Exception as error:
        row['failure'] = repr(error)
    finally:
        selector.close()
        if child.poll() is None:
            row['cleanup'] = force_stop(child)
        row['wallSeconds'] = time.monotonic() - started
        log.write_bytes(data)
    return row


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--repetitions', type=int, choices=(1, 8), default=1)
    parser.add_argument('--workers', type=int, choices=(1, 12), default=1)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    out = args.output.resolve()
    if os.uname().sysname != 'Darwin' or not out.is_relative_to(root / '.data') or out.exists():
        parser.error('fresh isolated Darwin output required')
    verify()
    prefix = root / '.data/d1510-fork-fd-consumer-prefix-v1'
    archive = prefix / 'lib/libgambit.a'
    receipt = json.loads((prefix / 'report.json').read_text())
    if not receipt['constructionQualified'] or sha(archive) != receipt['archiveSha256']:
        raise ValueError('private archive provenance mismatch')
    home = root / '.data/d1391-runtime-object-source/build'
    driver = root / '.data/d1510-shell-substitution/bin'
    original_hash = sha(home / 'lib/libgambit.a')
    out.mkdir()
    fixture = out / 'no-shebang'
    fixture.write_text('printf SCRIPT-OK; exit 13\n')
    fixture.chmod(0o755)
    source = out / 'consumer.scm'
    source.write_text('''
(do ((iteration 0 (+ iteration 1))) ((= iteration REPETITIONS))
(let ((environment (map (lambda (kv) (string-append (car kv) "=" (cdr kv)))
                        (get-environment-variables))))
  (for-each
    (lambda (settings)
      (with-exception-catcher
        (lambda (e) (write (list 'error (no-such-file-or-directory-exception? e)))
                    (newline) (force-output))
        (lambda ()
          (let* ((p (open-process settings)) (output (read-line p #f)) (status (process-status p)))
            (close-port p)
            (write (list 'child output status)) (newline) (force-output)))))
    (list
      (list path: "sh" arguments: (list "-c" "printf CHILD-OK; exit 7")
            environment: environment stdin-redirection: #t stdout-redirection: #t)
      (list path: "no-shebang" environment: environment stdin-redirection: #t stdout-redirection: #t)
      (list path: "no-shebang" environment: (list FIXTURE_PATH)
            stdin-redirection: #t stdout-redirection: #t)
      (list path: "definitely-missing-d1510" environment: environment
            stdin-redirection: #t stdout-redirection: #t)))))
(display "CONTROLS-OK") (newline) (force-output)
'''.replace('FIXTURE_PATH', json.dumps('PATH=' + str(out)))
       .replace('REPETITIONS', str(args.repetitions)))
    expected = ['(child "CHILD-OK" 1792)', '(child "SCRIPT-OK" 3328)',
                '(child "SCRIPT-OK" 3328)', '(error #t)'] * args.repetitions + ['CONTROLS-OK']
    env = build_environment()
    report = dict(consumerControlsQualified=False, performanceAdmitted=False,
                  testQualified=False, productionAdmitted=False, builds=[], runs=[],
                  sourceSha256=sha(source), gscSha256=sha(driver / 'gsc'),
                  archiveSha256=sha(archive), scope='compiled-scheme-process-controls',
                  repetitions=args.repetitions, workers=args.workers, waves=[])
    try:
        for role, lib in (('frozen', home / 'lib'), ('candidate', prefix / 'lib')):
            binary = out / role
            local = dict(env, GAMBOPT=f'~~bin={driver},~~lib={lib},~~include={home / "include"}')
            row = run([str(driver / 'gsc'), '-verbose', '-exe', '-o', str(binary), str(source)],
                      local, out / (role + '-compile.log'), 'consumer-compile')
            row['role'] = role
            if row['passed']:
                symbols = subprocess.check_output(['/usr/bin/nm', str(binary)], env=env, timeout=10).decode()
                deployed = ' U _proc_pidinfo' in symbols
                row.update(binarySha256=sha(binary), forkProbeLinked=deployed)
                row['passed'] = deployed == (role == 'candidate')
            report['builds'].append(row)
            print(json.dumps({k: v for k, v in row.items() if k != 'lines'}), flush=True)
            if not row['passed']:
                return 1
        local = dict(env, PATH=f'{out}:/usr/bin:/bin')
        for index, role in enumerate(('frozen', 'candidate', 'candidate', 'frozen')):
            started = time.monotonic()
            def worker(number):
                row = run([str(out / role)], local, out / f'{index}-{role}-{number}.log',
                          'consumer-process-controls')
                row.update(role=role, wave=index, worker=number,
                           passed=row['passed'] and row.get('lines') == expected)
                return row
            with ThreadPoolExecutor(max_workers=args.workers) as executor:
                rows = list(executor.map(worker, range(args.workers)))
            report['runs'].extend(rows)
            wave = dict(role=role, passed=all(row['passed'] for row in rows),
                        wallSeconds=time.monotonic() - started, workers=args.workers)
            report['waves'].append(wave)
            print(json.dumps(wave), flush=True)
            if not wave['passed']:
                return 1
        if sha(home / 'lib/libgambit.a') != original_hash or sha(archive) != report['archiveSha256']:
            raise ValueError('archive identity drift')
        verify()
        report['consumerControlsQualified'] = True
        return 0
    finally:
        (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    raise SystemExit(main())
