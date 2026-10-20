"""Merge a private os_io replacement with the exact frozen parser object."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

from bazel_host_environment import build_environment
from prepare_darwin_fork_fd import prepare
from progressive_performance_gate import force_stop
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
    component = json.loads((root / '.data/d1510-fork-fd-controls-v2/report.json').read_text())
    if not component['componentQualified'] or len(component['runs']) != 12:
        raise ValueError('FD semantics and concurrent controls not qualified')
    out.mkdir()
    home = root / '.data/d1391-runtime-object-source/build'
    lib = root / '.data/d1391-runtime-object-source/src/gambit/lib'
    driver = root / '.data/d1510-shell-substitution/bin'
    frozen = root / '.data/d1510-reader-batch-runtime-v1'
    original = lib / 'os_io.c'
    source = out / 'os_io_fd.c'
    source.write_text(prepare(original.read_text()))
    input_hashes = {str(path.relative_to(root)): sha(path) for path in (
        original, frozen / '_io.o', frozen / '_gambit.o', home / 'lib/libgambit.a')}
    report = dict(qualified=False, performanceAdmitted=False, productionAdmitted=False,
                  inputHashes=input_hashes, steps=[])
    env = build_environment()

    def run(name, command, local=env):
        started = time.monotonic()
        with (out / (name + '.log')).open('w') as log:
            child = subprocess.Popen(command, env=local, stdout=log, stderr=subprocess.STDOUT,
                                     start_new_session=True)
            try:
                child.wait(timeout=60)
            finally:
                if child.poll() is None:
                    force_stop(child)
        report['steps'].append(dict(name=name, exitCode=child.returncode,
                                  wallSeconds=time.monotonic() - started))
        print(json.dumps(report['steps'][-1]), flush=True)
        if child.returncode:
            raise RuntimeError(name)

    try:
        obj = source.with_suffix('.o')
        local = dict(env, GAMBITDIR_INCLUDE=str(home / 'include'), GAMBITDIR_LIB=str(home / 'lib'),
                     BUILD_OBJ_INPUT_FILENAMES_PARAM=str(source), BUILD_OBJ_OUTPUT_FILENAME_PARAM=str(obj),
                     BUILD_OBJ_META_INFO_FILE_PARAM=str(source),
                     BUILD_OBJ_CC_OPTIONS_PARAM=f'-O3 -D___LIBRARY -DHAVE_CONFIG_H -I{lib} -I{lib.parent / "include"}')
        run('compile-fork-fd', [str(driver / 'gambuild-C'), 'obj'], local)
        merged = out / 'runtime.o'
        run('merge-private-runtime', [env['CC'], '-r', '-o', str(merged),
                                     str(frozen / '_io.o'), str(obj)])
        shutil.copyfile(frozen / '_gambit.o', out / '_gambit.o')
        verify()
        if input_hashes != {relative: sha(root / relative) for relative in input_hashes}:
            raise ValueError('frozen input drift')
        report.update(qualified=True, objectSha256=sha(merged), sourceSha256=sha(source),
                      forkObjectSha256=sha(obj), runtimeLinkObjectSha256=sha(out / '_gambit.o'))
    finally:
        (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    main()
