#!/usr/bin/env python3
"""Baseline plus hardware-sized independent interpreter contract runs."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
from pathlib import Path
import subprocess
import time

from bazel_host_environment import build_environment


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[3]
    output = args.output.resolve()
    if not output.is_relative_to(repo / '.data'):
        parser.error('project-local receipts required')
    output.mkdir(parents=True, exist_ok=False)
    home = args.baseline.resolve() / 'build'
    candidate = args.candidate.resolve() / 'gxi'
    code = Path(__file__).with_name('gambit-bounded-eval-contract.scm').read_text()
    env = build_environment()
    env.update(GERBIL_HOME=str(home), GERBIL_LOADPATH=str(home / 'lib'),
               GAMBOPT=f"~~bin={home / 'bin'},~~lib={home / 'lib'},~~include={home / 'include'}")
    cores = int(subprocess.check_output(['sysctl', '-n', 'hw.physicalcpu'], text=True))
    report = dict(qualified=False, performanceQualified=False, cores=cores, runs=[])

    def run(name, binary):
        e = dict(env, GERBIL_PATH=str(output / f'user-{name}'),
                 GAMBIT_TRACE_COUNT_FILE=str(output / f'counts-{name}'))
        started = time.monotonic()
        result = subprocess.run([str(binary), '-e', code], env=e, text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=120)
        (output / f'{name}.log').write_text(result.stdout)
        if result.returncode or 'BOUNDED-EVAL-OK 3256' not in result.stdout or '*** ERROR' in result.stdout:
            raise RuntimeError(f'{name}: retained failing contract')
        row = dict(name=name, exitCode=result.returncode, wallSeconds=time.monotonic()-started)
        counter = output / f'counts-{name}.primitives-eval'
        if binary == candidate:
            row['hits'] = json.loads(counter.read_text())
            if any(row['hits'][kind] < 100 for kind in ('length', 'reverse', 'structure')):
                raise RuntimeError(f'{name}: interpreter primitive coverage absent')
        print(f'OK {name}', flush=True)
        return row

    try:
        report['runs'].append(run('baseline', home / 'bin/gxi'))
        with ThreadPoolExecutor(max_workers=cores) as pool:
            for future in as_completed([pool.submit(run, f'candidate-{i}', candidate) for i in range(cores)]):
                report['runs'].append(future.result())
        report['qualified'] = True
    except BaseException as error:
        report['failure'] = str(error)
        raise
    finally:
        (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    main()
