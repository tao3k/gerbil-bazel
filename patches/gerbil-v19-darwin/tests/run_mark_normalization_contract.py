"""Exercise the actual staging mark reducer, not a copied implementation."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess

from bazel_host_environment import build_environment


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--fixture', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    baseline, fixture, output = (path.resolve() for path in (args.baseline, args.fixture, args.output))
    if not all(path.is_relative_to(root / '.data') for path in (baseline, fixture, output)):
        parser.error('isolated .data paths required')
    output.mkdir(parents=True, exist_ok=False)
    home = baseline / 'build'
    binary = home / 'bin/gxi'
    env = build_environment()
    cores = int(subprocess.check_output(['sysctl', '-n', 'hw.physicalcpu'], text=True))
    env.update(GERBIL_HOME=str(home), GERBIL_LOADPATH=str(home / 'lib'),
               GERBIL_GSC=str(home / 'bin/gsc'),
               GAMBOPT=f"~~bin={home / 'bin'},~~lib={home / 'lib'},~~include={home / 'include'}")
    for key in list(env):
        if key.startswith('GAMBIT_'):
            env.pop(key)
    report = dict(qualified=False, performanceQualified=False, cores=cores, runs=[],
                  fixtureSha256=hashlib.sha256(fixture.read_bytes()).hexdigest(),
                  runtimeSha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
                  scope='actual-staging-mark-reducer-invariant-not-startup-performance')

    def check(index):
        log_path = output / f'native-{index}.log'
        process_env = dict(env, GERBIL_PATH=str(output / f'user-{index}'))
        with log_path.open('w') as log:
            child = subprocess.Popen([str(binary), str(fixture)], env=process_env,
                                     stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            try:
                code = child.wait(timeout=90)
            except subprocess.TimeoutExpired:
                os.killpg(child.pid, signal.SIGTERM)
                try:
                    child.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(child.pid, signal.SIGKILL)
                    child.wait()
                raise RuntimeError(f'native-{index} exceeded native contract budget')
        content = log_path.read_text()
        markers = ('CASE-OK all mark streams through length eight',
                   'HARNESS-OK actual mark normalization', 'MARK-NORMALIZATION-NATIVE-OK 9841')
        if code or not all(marker+'\n' in content for marker in markers):
            raise RuntimeError(f'native-{index} lacks explicit real std/test success')
        print('MARK-NORMALIZATION-CONTRACT-OK', index, flush=True)
        return dict(index=index, exitCode=code, testedStreams=9841, finalSuccess=True)

    try:
        with ThreadPoolExecutor(max_workers=cores) as pool:
            futures = [pool.submit(check, index) for index in range(cores)]
            for future in futures:
                report['runs'].append(future.result())
        report['qualified'] = True
    except BaseException as error:
        report['failure'] = str(error)
        raise
    finally:
        (output / 'report.json').write_text(json.dumps(report, indent=2)+'\n')


if __name__ == '__main__':
    main()
