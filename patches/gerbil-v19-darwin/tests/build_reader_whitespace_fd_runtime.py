"""Compose the three-cold-pass reader and qualified C FD component privately."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

from bazel_host_environment import build_environment
from progressive_performance_gate import force_stop
from summarize_three_time_gates import summarize
from verify_reader_batch_50_baseline import main as verify


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    out = args.output.resolve()
    if os.uname().sysname != 'Darwin' or not out.is_relative_to(root / '.data') or out.exists():
        parser.error('fresh isolated Darwin output required')
    verify()
    cold = json.loads((root / '.data/d1510-reader-whitespace-progressive-v1/report.json').read_text())
    if summarize(cold)['completeColdBuildGate'] != 'ALLOW':
        raise ValueError('three-passed reader cold builds required')
    reader = root / '.data/d1510-reader-whitespace-runtime-v2'
    fd = root / '.data/d1510-fork-fd-runtime-v1'
    reader_receipt = json.loads((reader / 'report.json').read_text())
    fd_receipt = json.loads((fd / 'report.json').read_text())
    inputs = [reader / '_io.o', reader / '_gambit.o', fd / 'os_io_fd.o']
    expected = [reader_receipt['objectSha256'], reader_receipt['runtimeLinkObjectSha256'],
                fd_receipt['forkObjectSha256']]
    if not reader_receipt['qualified'] or not fd_receipt['qualified'] or list(map(sha, inputs)) != expected:
        raise ValueError('component provenance mismatch')
    controls = json.loads((root / '.data/d1510-fork-fd-consumer-controls-v2/report.json').read_text())
    if not controls['consumerControlsQualified']:
        raise ValueError('compiled FD consumer controls required')
    out.mkdir()
    report = dict(qualified=False, performanceAdmitted=False, productionAdmitted=False,
                  inputHashes={str(path.relative_to(root)): sha(path) for path in inputs})
    env = build_environment()
    obj = out / 'runtime.o'
    started = time.monotonic()
    with (out / 'merge.log').open('w') as log:
        child = subprocess.Popen([env['CC'], '-r', '-o', str(obj), str(inputs[0]), str(inputs[2])],
                                 env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        try:
            child.wait(timeout=50)
        finally:
            if child.poll() is None:
                report['cleanup'] = force_stop(child)
    try:
        if child.returncode:
            raise RuntimeError('private runtime merge failed')
        shutil.copyfile(inputs[1], out / '_gambit.o')
        if list(map(sha, inputs)) != expected:
            raise ValueError('component input drift')
        verify()
        report.update(qualified=True, objectSha256=sha(obj),
                      runtimeLinkObjectSha256=sha(out / '_gambit.o'),
                      wallSeconds=time.monotonic() - started)
    finally:
        (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
