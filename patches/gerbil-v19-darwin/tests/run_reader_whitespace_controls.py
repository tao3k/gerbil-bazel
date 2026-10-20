"""Source/native mode contract with selected GNU tools and hard progress gates."""
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--binary', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    binary, out = args.binary.resolve(), args.output.resolve()
    if any(not path.is_relative_to(root / '.data') for path in (binary, out)) or out.exists():
        parser.error('selected binary and fresh persistent .data output required')
    digest = hashlib.sha256(binary.read_bytes()).hexdigest()
    receipt = json.loads((binary.parent / 'report.json').read_text())
    if not receipt['qualified'] or digest != receipt['binarySha256']:
        raise ValueError('construction identity mismatch')
    out.mkdir()
    home = root / '.data/d1391-runtime-object-source/build'
    driver = root / '.data/d1510-shell-substitution/bin'
    env = build_environment()
    env.update(GERBIL_HOME=str(home), GERBIL_LOADPATH=str(home / 'lib'),
               GERBIL_GSC=str(driver / 'gsc'), PHI_CONTROL_DIRECTORY=str(out),
               PATH=f'{binary.parent}:{driver}:{home / "bin"}:{env["PATH"]}',
               GAMBOPT=f'~~bin={driver},~~lib={home / "lib"},~~include={home / "include"}')
    env['READER_TOKEN_CONTROLS'] = str(Path(__file__).with_name('darwin_reader_batch_controls.scm'))
    controls = Path(__file__).with_name('darwin_reader_whitespace_controls.scm')
    expected_cases = 45
    started = time.monotonic()
    gate = ProgressiveGate(Limits('phi-native-source-controls', silence=5), started)
    process = subprocess.Popen([str(binary.parent / 'gxi'), '-e',
                                '(load ' + json.dumps(str(controls)) + ')'], env=env,
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT, start_new_session=True)
    report = dict(semanticControlsPassed=False, performanceAdmitted=False, binarySha256=digest)
    selector = selectors.DefaultSelector()
    selector.register(process.stdout, selectors.EVENT_READ)
    try:
        with (out / 'controls.log').open('wb') as log:
            while selector.get_map() or process.poll() is None:
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
        status = process.wait(timeout=1)
        text = (out / 'controls.log').read_text(errors='replace')
        cases = [line[8:] for line in text.splitlines() if line.startswith('CASE-OK ')]
        report.update(exitCode=status, cases=cases,
                      semanticControlsPassed=(status == 0 and len(cases) == len(set(cases)) == expected_cases and
                                              text.splitlines()[-1:] == ['OK'] and '*** ERROR' not in text))
    except Exception as error:
        report['failure'] = repr(error)
        if isinstance(error, GateViolation):
            report['performanceStop'] = error.record
    finally:
        selector.close()
        if process.poll() is None:
            report['cleanup'] = force_stop(process)
        report['wallSeconds'] = time.monotonic() - started
        (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))
    return 0 if report['semanticControlsPassed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
