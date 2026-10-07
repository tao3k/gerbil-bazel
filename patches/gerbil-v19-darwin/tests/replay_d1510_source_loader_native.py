"""Replay the measured generated-driver change on retained D1510 inputs."""
import hashlib
import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'patches/gerbil-v19-darwin/tests'))
from bazel_host_environment import build_environment
from gambit_host_coalescing import render

HOME = ROOT / '.data/d1391-runtime-object-source/build'
parser = argparse.ArgumentParser()
parser.add_argument('--output', default='.data/d1510-source-loader-replay')
args = parser.parse_args()
OUT = ROOT / args.output
assert OUT.resolve().is_relative_to(ROOT / '.data')
OUT.mkdir()
env = build_environment()
cores = int(subprocess.check_output(['sysctl', '-n', 'hw.physicalcpu'], text=True))
env.update(GERBIL_HOME=str(HOME), GERBIL_LOADPATH=str(HOME / 'lib'),
           GERBIL_BUILD_CORES=str(cores),
           GAMBOPT=f'~~bin={HOME}/bin,~~lib={HOME}/lib,~~include={HOME}/include')
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
baseline = json.loads((ROOT / '.data/d1510-outline-current-native/report.json').read_text())
original_hashes = baseline['inputHashes']
assert original_hashes == {p: sha(ROOT / p) for p in original_hashes}
report = dict(qualified=False, performanceQualified=False, cores=cores,
              scope='retained-native-source-loader-not-performance-admission',
              inputHashes=original_hashes, steps=[], runtimeArchiveSha256=sha(HOME / 'lib/libgambit.a'))

def run(name, command, local_env=env, budget=180):
    started = time.monotonic()
    with (OUT / (name + '.log')).open('w') as log:
        child = subprocess.Popen(command, env=local_env, stdout=log,
                                 stderr=subprocess.STDOUT, start_new_session=True)
        try:
            child.wait(timeout=budget)
        finally:
            if child.poll() is None:
                os.killpg(child.pid, signal.SIGTERM)
                try:
                    child.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    os.killpg(child.pid, signal.SIGKILL)
                    child.wait()
    report['steps'].append(dict(name=name, exitCode=child.returncode,
                               wallSeconds=time.monotonic()-started))
    print(json.dumps(report['steps'][-1]), flush=True)
    if child.returncode:
        raise RuntimeError(name)

try:
    stem = 'gerbil__compiler__driver'
    scm = OUT / (stem + '.scm')
    original = (HOME / 'lib/static' / (stem + '.scm')).read_text()
    anchor = '(gxc#compile-scm-file__0\n                                _%scmrt275742%_\n                                _%loader-code275738%_)'
    assert original.count(anchor) == 1
    helper = (ROOT / 'patches/gerbil-v19-darwin/tests/d1510-source-loader-helper.scm').read_text()
    original = original.replace(anchor, '(gxc#compile-generated-loader\n                                _%scmrt275742%_\n                                _%loader-code275738%_)')
    scm.write_text('(declare (block) (standard-bindings) (extended-bindings))\n' + helper + original)
    cfile = scm.with_suffix('.c')
    obj = scm.with_suffix('.o')
    run('generate-init', [str(HOME / 'bin/gsc'), '-c', '-o', str(cfile), str(scm)])
    objenv = dict(env, GAMBITDIR_INCLUDE=str(HOME / 'include'), GAMBITDIR_LIB=str(HOME / 'lib'),
                  BUILD_OBJ_INPUT_FILENAMES_PARAM=str(cfile), BUILD_OBJ_OUTPUT_FILENAME_PARAM=str(obj),
                  BUILD_OBJ_CC_OPTIONS_PARAM='-O1', BUILD_OBJ_META_INFO_FILE_PARAM=str(cfile))
    run('compile-init', [str(HOME / 'bin/gambuild-C'), 'obj'], objenv)
    order = json.loads((ROOT / '.data/d994-parameter-native-trace-profile/module-order.log').read_text().splitlines()[-1])
    modules = [*order, 'gerbil/main']
    sources = [cfile if module == 'gerbil/compiler/driver' else
               HOME / 'lib/static' / (module.replace('/', '__') + '.c') for module in modules]
    link = OUT / 'gerbil-link-original.c'
    run('generate-link', [str(HOME / 'bin/gsc'), '-link', '-track-scheme', '-o', str(link), *map(str, sources)])
    prior = json.loads((ROOT / '.data/d1083-outlined-inherited-uninstrumented/report.json').read_text())
    selected = {row['module'] for row in prior['objects']}
    paths = [path for path in sources if path.stem.replace('__', '/') in selected]
    assert len(paths) == 11 and cfile not in paths
    content, details = render(paths, link.read_text(), OUT,
        guarded_readonly_traces=True, guarded_trace_polls=True,
        guarded_trace_restart_polls=True, guarded_trace_coalesce_polls=True,
        guarded_trace_primitive_boundary=True, guarded_trace_inline_lookup=True,
        guarded_trace_outline_lookup=True, guarded_trace_lookup_return_branches=True,
        parameter_entry_fastpath=True, parameter_identity_return=True,
        parameter_env_lookup=True, bounded_primitive_entries=True,
        guarded_trace_outline_returns=False)
    carrier = OUT / 'gerbil-link.c'
    carrier.write_text(content)
    objenv.update(BUILD_OBJ_INPUT_FILENAMES_PARAM=str(carrier),
                  BUILD_OBJ_OUTPUT_FILENAME_PARAM=str(OUT / 'gerbil-link.o'),
                  BUILD_OBJ_META_INFO_FILE_PARAM=str(carrier))
    run('compile-carrier', [str(HOME / 'bin/gambuild-C'), 'obj'], objenv, budget=900)
    objects = [obj if module == 'gerbil/compiler/driver' else
               HOME / 'lib/static' / (module.replace('/', '__') + '.o') for module in modules]
    run('link-native', [env['CC'], '-o', str(OUT / 'gerbil'), *map(str, objects),
                       str(OUT / 'gerbil-link.o'), str(HOME / 'lib/libgambit.a'), '-ldl', '-lm'])
    (OUT / 'gxi').symlink_to('gerbil')
    run('smoke', [str(OUT / 'gxi'), '-e', '(import :std/test :std/make) (if (not (gxc#darwin-gnu-source-loader-platform?)) (error "candidate inactive")) (displayln "IMPORT-OK")'])
    assert (OUT / 'smoke.log').read_text().splitlines()[-1] == 'IMPORT-OK'
    report['baselineUnchanged'] = original_hashes == {p: sha(ROOT / p) for p in original_hashes}
    assert report['baselineUnchanged']
    report.update(qualified=True, binarySha256=sha(OUT / 'gerbil'),
                  gscSha256=sha(HOME / 'bin/gsc'), helperSha256=sha(ROOT / 'patches/gerbil-v19-darwin/tests/d1510-source-loader-helper.scm'))
finally:
    (OUT / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
