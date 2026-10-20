"""Cross-process code serialization controls, not a performance admission."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import selectors
import subprocess
import time

from bazel_host_environment import build_environment
from progressive_performance_gate import ProgressiveGate, Limits, force_stop


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--binary', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--parsed-ssi', action='store_true')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    binary, out = args.binary.resolve(), args.output.resolve()
    if not binary.is_relative_to(root / '.data') or not out.is_relative_to(root / '.data') or out.exists():
        parser.error('isolated selected binary and fresh output required')
    construction = json.loads((binary.parent / 'report.json').read_text())
    digest = hashlib.sha256(binary.read_bytes()).hexdigest()
    if not construction['qualified'] or digest != construction['binarySha256']:
        raise ValueError('selected native construction drift')
    env = build_environment()
    home = root / '.data/d1391-runtime-object-source/build'
    driver = root / '.data/d1510-shell-substitution/bin'
    env.update(GERBIL_HOME=str(home), GERBIL_LOADPATH=str(home / 'lib'),
               PHI_BLOB_PATH=str(out / 'module.bin'),
               PHI_SSI_PATH=str(home / 'lib/std/make.ssi'),
               GAMBOPT=f'~~bin={driver},~~lib={home / "lib"},~~include={home / "include"}')
    out.mkdir()
    report = dict(qualified=False, performanceAdmitted=False, binarySha256=digest, runs=[])
    try:
        for name, count in [('producer', 3), ('consumer', 8), ('consumer', 8)]:
            index = len(report['runs'])
            prefix = 'parsed_ssi_blob' if args.parsed_ssi else 'compiled_phi_blob'
            fixture = Path(__file__).with_name(f'{prefix}_{name}.scm')
            started = time.monotonic()
            gate = ProgressiveGate(Limits('compiled-phi-' + name, silence=5), started)
            child = subprocess.Popen([str(binary.parent / 'gxi'), '-e', '(load ' + json.dumps(str(fixture)) + ')'],
                                     env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, start_new_session=True)
            selector = selectors.DefaultSelector()
            selector.register(child.stdout, selectors.EVENT_READ)
            logpath = out / (str(index) + '-' + name + '.log')
            row = dict(name=name, passed=False)
            try:
                with logpath.open('wb') as log:
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
                text = logpath.read_text(errors='replace')
                cases = [line[8:] for line in text.splitlines() if line.startswith('CASE-OK ')]
                row.update(cases=cases, passed=(row['exitCode'] == 0 and len(cases) == len(set(cases)) == count
                           and text.splitlines()[-1:] == ['OK'] and '*** ERROR' not in text))
            finally:
                selector.close()
                if child.poll() is None:
                    row['cleanup'] = force_stop(child)
                row['wallSeconds'] = time.monotonic() - started
                report['runs'].append(row)
            print(json.dumps(row), flush=True)
            if not row['passed']:
                return 1
        report['qualified'] = True
        return 0
    finally:
        (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    raise SystemExit(main())
