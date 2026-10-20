#!/usr/bin/env python3
"""Isolated original-ABI Gambit interpreter override of a qualified carrier."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import signal
import subprocess
import time

from bazel_host_environment import build_environment
from gambit_bounded_primitives import inject_runtime_unit


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--carrier', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--count', action='store_true')
    args = parser.parse_args()
    baseline, carrier, output = (p.resolve() for p in (args.baseline, args.carrier, args.output))
    repo = Path(__file__).resolve().parents[3]
    if platform.system() != 'Darwin' or not output.is_relative_to(repo / '.data'):
        parser.error('isolated Darwin .data output required')
    prior = json.loads((carrier / 'report.json').read_text())
    if not prior.get('qualified') or not prior.get('boundedPrimitiveEntries'):
        parser.error('qualified bounded-primitive carrier required')
    output.mkdir(parents=True, exist_ok=False)
    digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    env = build_environment()
    macros = subprocess.check_output([env['CC'], '-dM', '-E', '-x', 'c', os.devnull], env=env, text=True)
    if '#define __clang__' in macros or '#define __GNUC__ 16\n' not in macros:
        raise RuntimeError('real GNU GCC 16 required')
    home = baseline / 'build'
    env.update(GERBIL_HOME=str(home), GERBIL_LOADPATH=str(home / 'lib'),
               GERBIL_PATH=str(output / 'empty-user'),
               GAMBOPT=f"~~bin={home / 'bin'},~~lib={home / 'lib'},~~include={home / 'include'}",
               PATH=f"{home / 'bin'}:{env['PATH']}")
    source = baseline / 'src/gambit/lib/_eval.c'
    content, details = inject_runtime_unit(source.read_text(), source)
    if args.count:
        content = r'''
#include <stdio.h>
#include <stdlib.h>
static unsigned long gb_eval_counts[3],gb_eval_reverse_pairs;
#define GB_BOUNDED_PRIMITIVE_HIT(kind,size) do { ++gb_eval_counts[kind]; if ((kind)==1) gb_eval_reverse_pairs+=(size); } while (0)
static void __attribute__((destructor)) gb_eval_count_dump(void) {
  const char *path=getenv("GAMBIT_TRACE_COUNT_FILE");
  char name[4096];
  if (path && snprintf(name,sizeof(name),"%s.primitives-eval",path)<sizeof(name)) {
    FILE *file=fopen(name,"w");
    if (file) {
      fprintf(file,"{\"length\":%lu,\"reverse\":%lu,\"structure\":%lu,\"reversePairs\":%lu}\n",
        gb_eval_counts[0],gb_eval_counts[1],gb_eval_counts[2],gb_eval_reverse_pairs);
      fclose(file);
    }
  }
}
''' + content
    generated = output / '_eval.c'
    generated.write_text(content)
    modules = json.loads((carrier / 'module-order.log').read_text().splitlines()[-1])
    static = carrier / 'source/build/lib/static'
    objects = [static / (m.replace('/', '__') + '.o') for m in [*modules, 'gerbil/main']]
    for row in prior['objects']:
        stem = static / row['module'].replace('/', '__')
        if digest(stem.with_suffix('.o')) != row['objectSha256']:
            raise RuntimeError('carrier object drift')
    report = dict(qualified=False, performanceQualified=False, diagnosticOnly=args.count,
                  originalGeneratedCSha256=digest(source), generatedCSha256=digest(generated),
                  carrierBinarySha256=prior['binaryHashes']['gxi'],
                  originalOptimization='O1', consumerFlagsChanged=False, runs=[], **details)

    def run(name, command, process_env=env):
        started = time.monotonic()
        with (output / f'{name}.log').open('w') as log:
            child = subprocess.Popen(command, env=process_env, stdout=log, stderr=subprocess.STDOUT,
                                     start_new_session=True)
            try:
                while child.poll() is None:
                    try:
                        child.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        print(f'ACTIVE {name}: {time.monotonic()-started:.1f}s', flush=True)
                    if child.poll() is None and time.monotonic()-started > 600:
                        raise TimeoutError(f'{name} exceeded 600 seconds')
            finally:
                if child.poll() is None:
                    os.killpg(child.pid, signal.SIGTERM)
                    try:
                        child.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        os.killpg(child.pid, signal.SIGKILL)
                        child.wait()
        report['runs'].append(dict(name=name, exitCode=child.returncode,
                                   wallSeconds=time.monotonic()-started))
        if child.returncode:
            raise RuntimeError(f'{name} failed: {child.returncode}')
        print(f'OK {name}', flush=True)

    try:
        e = dict(env, GAMBITDIR_INCLUDE=str(home / 'include'), GAMBITDIR_LIB=str(home / 'lib'),
                 BUILD_OBJ_INPUT_FILENAMES_PARAM=str(generated),
                 BUILD_OBJ_OUTPUT_FILENAME_PARAM=str(generated.with_suffix('.o')),
                 BUILD_OBJ_META_INFO_FILE_PARAM=str(generated),
                 BUILD_OBJ_CC_OPTIONS_PARAM=f'-O1 -D___LIBRARY -D___PRIMAL -DHAVE_CONFIG_H -I{baseline / "src/gambit/lib"} -I{baseline / "src/gambit/include"}')
        run('compile-eval', [str(home / 'bin/gambuild-C'), 'obj'], e)
        binary = output / 'gerbil'
        run('link-eval', [env['CC'], '-o', str(binary), *map(str, objects),
                          str(carrier / 'gerbil-link.o'), str(generated.with_suffix('.o')),
                          f'-L{home / "lib"}', '-lgambit', '-ldl', '-lm'])
        (output / 'gxi').symlink_to('gerbil')
        (output / 'build/bin').mkdir(parents=True)
        (output / 'build/bin/gxi').symlink_to('../../gerbil')
        run('import-smoke', [str(output / 'gxi'), '-e',
                            '(import :std/make :std/test :std/build-script) (displayln "IMPORT-OK")'])
        if not (output / 'import-smoke.log').read_text().rstrip().endswith('IMPORT-OK'):
            raise RuntimeError('native import smoke failed')
        report['binarySha256'] = digest(binary)
        report['qualified'] = True
    except BaseException as error:
        report['failure'] = str(error)
        raise
    finally:
        (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    main()
