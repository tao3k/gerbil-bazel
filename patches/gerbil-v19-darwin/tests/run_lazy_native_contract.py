"""Native staged-module prerequisite, not a Gerbil build/test speed claim."""
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
from verify_source_loader_49_baseline import main as verify


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--dynamic-providers', action='store_true')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    output = args.output.resolve()
    if not output.is_relative_to(root / '.data') or output.exists():
        parser.error('fresh isolated .data output required')
    if os.uname().sysname != 'Darwin':
        parser.error('Darwin-only architecture control')
    output.mkdir()
    verify()
    home = root / '.data/d1391-runtime-object-source/build'
    driver = root / '.data/d1510-shell-substitution/bin'
    env = build_environment()
    env.update(GAMBOPT=f'~~bin={driver},~~lib={home / "lib"},~~include={home / "include"}')
    report = dict(qualified=False, performanceAdmitted=False,
                  scope='native-deferred-module-semantic-prerequisite-only',
                  dynamicProviders=args.dynamic_providers, steps=[])

    def run(name, command, local_env=env, limit=52, cwd=None):
        started = time.monotonic()
        with (output / (name + '.log')).open('w') as log:
            process = subprocess.Popen(command, env=local_env, cwd=cwd, stdout=log,
                                       stderr=subprocess.STDOUT, start_new_session=True)
            try:
                process.wait(timeout=limit)
            finally:
                if process.poll() is None:
                    force_stop(process)
        row = dict(name=name, exitCode=process.returncode,
                   wallSeconds=time.monotonic() - started)
        report['steps'].append(row)
        print(json.dumps(row), flush=True)
        if process.returncode:
            raise RuntimeError(name)

    try:
        names = ['lazy_native_dependency', 'lazy_native_payload',
                 'lazy_native_failure', 'lazy_native_main']
        sources = []
        objects = []
        for name in names:
            source = output / (name + '.scm')
            shutil.copy2(Path(__file__).with_name(name + '.scm'), source)
            cfile, obj = source.with_suffix('.c'), source.with_suffix('.o')
            run('generate-' + name, [str(driver / 'gsc'), '-c', '-o', str(cfile), str(source)])
            compile_env = dict(env, GAMBITDIR_INCLUDE=str(home / 'include'),
                               GAMBITDIR_LIB=str(home / 'lib'),
                               BUILD_OBJ_INPUT_FILENAMES_PARAM=str(cfile),
                               BUILD_OBJ_OUTPUT_FILENAME_PARAM=str(obj),
                               BUILD_OBJ_CC_OPTIONS_PARAM=('-O1 -D___DYNAMIC' if
                                   args.dynamic_providers and name != 'lazy_native_main' else '-O1'),
                               BUILD_OBJ_META_INFO_FILE_PARAM=str(cfile))
            run('compile-' + name, [str(driver / 'gambuild-C'), 'obj'], compile_env)
            sources.append(cfile)
            objects.append(obj)
        link = output / 'lazy_native_link.c'
        specs = ['(' + json.dumps(str(path)) + ' (preload . #f))' for path in sources[:-1]]
        specs.append(json.dumps(str(sources[-1])))
        expression = "(link-incremental '(" + ' '.join(specs) + ') output: ' + json.dumps(str(link)) + ')'
        run('generate-link', [str(driver / 'gsc'), '-e', expression])
        link_text = link.read_text()
        if link_text.count('___DEF_LNK_NOPRELOAD(') != 3:
            raise ValueError('all three provider modules must retain deferred flags')
        link_env = dict(compile_env, BUILD_OBJ_INPUT_FILENAMES_PARAM=str(link),
                        BUILD_OBJ_OUTPUT_FILENAME_PARAM=str(link.with_suffix('.o')),
                        BUILD_OBJ_CC_OPTIONS_PARAM='-O1 -D___APPLICATION',
                        BUILD_OBJ_META_INFO_FILE_PARAM=str(link))
        run('compile-link', [str(driver / 'gambuild-C'), 'obj'], link_env)
        binary = output / 'lazy-native-controls'
        run('link-native', [env['CC'], '-o', str(binary), *map(str, objects),
                            str(link.with_suffix('.o')), str(home / 'lib/libgambit.a'), '-ldl', '-lm'])
        empty = output / 'empty-working-directory'
        empty.mkdir()
        run('controls', [str(binary)], cwd=empty)
        text = (output / 'controls.log').read_text()
        cases = [line[8:] for line in text.splitlines() if line.startswith('CASE-OK ')]
        report.update(cases=cases, binarySha256=hashlib.sha256(binary.read_bytes()).hexdigest())
        if len(cases) != 13 or len(set(cases)) != 13 or text.splitlines()[-1:] != ['OK']:
            raise ValueError('native control case inventory or terminal status failed')
        verify()
        report.update(qualified=True, baselineUnchanged=True)
    finally:
        (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
