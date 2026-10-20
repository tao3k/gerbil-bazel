"""Isolated FD semantics and concurrent component evidence, not suite admission."""
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
from progressive_performance_gate import GateViolation, Limits, ProgressiveGate, force_stop


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    out = args.output.resolve()
    if os.uname().sysname != 'Darwin' or not out.is_relative_to(root / '.data') or out.exists():
        parser.error('fresh isolated Darwin output required')
    out.mkdir()
    env = build_environment()
    binary = out / 'controls'
    source = Path(__file__).with_name('darwin_fork_fd_controls.c')
    with (out / 'compile.log').open('w') as log:
        subprocess.run([env['CC'], '-O3', '-Wall', '-Wextra', '-Werror', str(source), '-o', str(binary)],
                       env=env, stdout=log, stderr=subprocess.STDOUT, check=True, timeout=30)
    cores = int(subprocess.check_output(['sysctl', '-n', 'hw.physicalcpu'], text=True))

    def run(index):
        started = time.monotonic()
        gate = ProgressiveGate(Limits('fd-component-controls', complete=50, first=5, silence=5), started)
        child = subprocess.Popen([str(binary)], env=env, stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT, start_new_session=True)
        selector = selectors.DefaultSelector()
        selector.register(child.stdout, selectors.EVENT_READ)
        row = dict(passed=False, index=index)
        try:
            with (out / f'{index}.log').open('wb') as log:
                while selector.get_map() or child.poll() is None:
                    gate.check(time.monotonic())
                    for key, _ in selector.select(.05):
                        chunk = os.read(key.fileobj.fileno(), 65536)
                        if not chunk:
                            selector.unregister(key.fileobj)
                            continue
                        now = time.monotonic()
                        gate.output(now)
                        gate.first(now)
                        log.write(chunk)
                        log.flush()
            gate.check(time.monotonic())
            row['exitCode'] = child.wait(timeout=1)
            text = (out / f'{index}.log').read_text()
            row['cases'] = [line for line in text.splitlines() if line.startswith('CASE-OK ')]
            row['passed'] = row['exitCode'] == 0 and len(row['cases']) == 8 and text.splitlines()[-1:] == ['OK']
        except Exception as error:
            row['failure'] = repr(error)
            if isinstance(error, GateViolation):
                row['performanceStop'] = error.record
        finally:
            selector.close()
            if child.poll() is None:
                row['cleanup'] = force_stop(child)
            row['wallSeconds'] = time.monotonic() - started
        return row

    started = time.monotonic()
    with ThreadPoolExecutor(max_workers=cores) as pool:
        rows = list(pool.map(run, range(cores)))
    report = dict(componentQualified=all(row['passed'] for row in rows),
                  performanceAdmitted=False, testQualified=False, productionAdmitted=False,
                  cores=cores, waveWallSeconds=time.monotonic() - started, runs=rows,
                  binarySha256=hashlib.sha256(binary.read_bytes()).hexdigest())
    (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({key: value for key, value in report.items() if key != 'runs'}))
    return 0 if report['componentQualified'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
