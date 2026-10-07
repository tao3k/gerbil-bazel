"""Compile one private Gambit runtime object using its configured library prelude."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time

from bazel_host_environment import build_environment
from prepare_generated_phi_eval import prepare
from prepare_darwin_reader_batch import prepare as prepare_reader
from progressive_performance_gate import force_stop
from verify_source_loader_49_baseline import main as verify


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--compiled-phi', action='store_true')
    parser.add_argument('--reader-batch', action='store_true')
    args = parser.parse_args()
    if args.reader_batch and args.compiled_phi:
        parser.error('distinct runtime experiments must not be mixed')
    root = Path(__file__).resolve().parents[3]
    out = args.output.resolve()
    if os.uname().sysname != 'Darwin' or not out.is_relative_to(root / '.data') or out.exists():
        parser.error('fresh isolated Darwin output required')
    verify()
    out.mkdir()
    home = root / '.data/d1391-runtime-object-source/build'
    lib = root / '.data/d1391-runtime-object-source/src/gambit/lib'
    driver = root / '.data/d1510-shell-substitution/bin'
    module = '_io' if args.reader_batch else '_eval'
    original = lib / (module + '.scm')
    scm = out / (module + '.scm')
    scm.write_text(prepare_reader(original.read_text()) if args.reader_batch else prepare(original.read_text(), args.compiled_phi))
    report = dict(qualified=False, productionAdmitted=False, steps=[], originalSha256=sha(original))
    env = build_environment()
    env.update(GERBIL_HOME=str(home), GERBIL_LOADPATH=str(home / 'lib'),
               GAMBOPT=f'~~bin={driver},~~lib={lib},~~include={home / "include"}')

    def run(name, command, local=env):
        started = time.monotonic()
        with (out / (name + '.log')).open('w') as log:
            child = subprocess.Popen(command, env=local, stdout=log, stderr=subprocess.STDOUT,
                                     start_new_session=True)
            try:
                child.wait(timeout=180)
            finally:
                if child.poll() is None:
                    force_stop(child)
        report['steps'].append(dict(name=name, exitCode=child.returncode,
                                  wallSeconds=time.monotonic() - started))
        print(json.dumps(report['steps'][-1]), flush=True)
        if child.returncode:
            raise RuntimeError(name)

    try:
        make = (lib / 'makefile').read_text()
        value = re.search(r'^PRELUDE_OPT = -prelude "(.*)"$', make, re.M).group(1)
        prelude = value.replace('$(srcdirpfx)../lib/header.scm', str(lib / 'header.scm'))
        prelude = prelude.replace('\\#', '#').replace('\\"', '"')
        if args.reader_batch:
            prelude = '(define-cond-expand-feature|darwin-gnu-reader-batch|)' + prelude
        cfile, obj = scm.with_suffix('.c'), scm.with_suffix('.o')
        run('generate-eval', [str(driver / 'gsc'), '-f', '-c', '-o', str(cfile),
                              '-prelude', prelude, str(scm)])
        local = dict(env, GAMBITDIR_INCLUDE=str(home / 'include'), GAMBITDIR_LIB=str(home / 'lib'),
                     BUILD_OBJ_INPUT_FILENAMES_PARAM=str(cfile), BUILD_OBJ_OUTPUT_FILENAME_PARAM=str(obj),
                     BUILD_OBJ_META_INFO_FILE_PARAM=str(cfile),
                     BUILD_OBJ_CC_OPTIONS_PARAM=f'-O1 -D___LIBRARY -D___PRIMAL -DHAVE_CONFIG_H -I{lib} -I{lib.parent / "include"}')
        run('compile-eval', [str(driver / 'gambuild-C'), 'obj'], local)
        # The platform probe adds one C-procedure global; regenerate its RTS table.
        def globals_in(path):
            return set(re.findall(r'^___DEF_GLO\(\d+,(.*)\)$', path.read_text(), re.M))
        original_globals, fresh_globals = globals_in(lib / (module + '.c')), globals_in(cfile)
        added_globals = {'"_eval#0"', '"_eval#1"'} if args.compiled_phi else {'"_eval#0"'}
        if args.compiled_phi:
            added_globals.update('"' + name + '"' for name in (
                'read-subu8vector', '##error', 'file-info-size',
                '##u8vector->object', '##make-u8vector', 'file-info', '##call-with-input-file'))
        if args.reader_batch:
            actual = fresh_globals - original_globals
            required = {'"##gb-darwin-token-scan"', '"##gb-darwin-token-copy"', '"##gb-darwin-buffered-token"'}
            native_entries = {name for name in actual if re.fullmatch(r'"_io#\d+"', name)}
            if len(native_entries) != 2:
                raise ValueError('expected two bounded native token entry points')
            added_globals = required | native_entries
        if not original_globals or original_globals - fresh_globals or fresh_globals - original_globals != added_globals:
            raise ValueError('unexpected runtime global interface change')
        modules = ['_kernel', '_system', '_num', '_std', '_eval', '_module', '_io', '_nonstd', '_thread', '_repl']
        link = out / '_gambit.c'
        run('generate-runtime-link', [str(driver / 'gsc'), '-f', '-warnings', '-link', '-flat',
                                     '-o', str(link), '-preload',
                                     *map(str, [cfile if name == module else lib / (name + '.c') for name in modules])])
        local.update(BUILD_OBJ_INPUT_FILENAMES_PARAM=str(link),
                     BUILD_OBJ_OUTPUT_FILENAME_PARAM=str(link.with_suffix('.o')),
                     BUILD_OBJ_META_INFO_FILE_PARAM=str(link))
        run('compile-runtime-link', [str(driver / 'gambuild-C'), 'obj'], local)
        verify()
        if sha(original) != report['originalSha256']:
            raise ValueError('original runtime source changed')
        report.update(qualified=True, objectSha256=sha(obj), sourceSha256=sha(scm),
                      generatedCSha256=sha(cfile), originalGlobals=len(original_globals),
                      runtimeLinkObjectSha256=sha(link.with_suffix('.o')))
    finally:
        (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
