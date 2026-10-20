"""Isolated one-module experiment on the frozen D1510 source-loader recipe."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import time

from bazel_host_environment import build_environment
from gambit_host_coalescing import render
from progressive_performance_gate import force_stop
from verify_source_loader_49_baseline import main as verify_anchor


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--module', choices=('gerbil/expander/stxcase', 'gerbil/compiler/driver'),
                        default='gerbil/expander/stxcase')
    parser.add_argument('--activation', default='(and splice-cursor-enabled? (splice-cursor-canonical?))')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    source, out = args.source.resolve(), args.output.resolve()
    if any(not path.is_relative_to(root / '.data') for path in (source, out)) or out.exists():
        parser.error('isolated source and fresh output required')
    verify_anchor()
    home = root / '.data/d1391-runtime-object-source/build'
    baseline = json.loads((root / '.data/d1510-outline-current-native/report.json').read_text())
    sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    original_hashes = baseline['inputHashes']
    out.mkdir()
    env = build_environment()
    cores = int(subprocess.check_output(['sysctl', '-n', 'hw.physicalcpu'], text=True))
    env.update(GERBIL_HOME=str(home), GERBIL_LOADPATH=str(home / 'lib'),
               GERBIL_BUILD_CORES=str(cores),
               GAMBOPT=f'~~bin={home}/bin,~~lib={home}/lib,~~include={home}/include')
    report = dict(qualified=False, performanceQualified=False, cores=cores,
                  scope='isolated-single-module-construction-only', module=args.module,
                  inputHashes=original_hashes, steps=[], sourceSha256=sha(source),
                  runtimeArchiveSha256=sha(home / 'lib/libgambit.a'))

    def run(name, command, local_env=env, budget=180):
        started = time.monotonic()
        with (out / (name + '.log')).open('w') as log:
            child = subprocess.Popen(command, env=local_env, stdout=log,
                                     stderr=subprocess.STDOUT, start_new_session=True)
            try:
                child.wait(timeout=budget)
            finally:
                if child.poll() is None:
                    force_stop(child)
        report['steps'].append(dict(name=name, exitCode=child.returncode,
                                  wallSeconds=time.monotonic() - started))
        print(json.dumps(report['steps'][-1]), flush=True)
        if child.returncode:
            raise RuntimeError(name)

    try:
        module = args.module
        scm = out / (module.replace('/', '__') + '.scm')
        shutil.copy2(source, scm)
        cfile, obj = scm.with_suffix('.c'), scm.with_suffix('.o')
        run('generate-stxcase', [str(home / 'bin/gsc'), '-c', '-o', str(cfile), str(scm)])
        objenv = dict(env, GAMBITDIR_INCLUDE=str(home / 'include'), GAMBITDIR_LIB=str(home / 'lib'),
                      BUILD_OBJ_INPUT_FILENAMES_PARAM=str(cfile), BUILD_OBJ_OUTPUT_FILENAME_PARAM=str(obj),
                      BUILD_OBJ_CC_OPTIONS_PARAM='-O1', BUILD_OBJ_META_INFO_FILE_PARAM=str(cfile))
        run('compile-stxcase', [str(home / 'bin/gambuild-C'), 'obj'], objenv)
        retained = root / '.data/d1510-source-loader-linked/gerbil__compiler__driver'
        replacements = {module: (cfile, obj)}
        if module != 'gerbil/compiler/driver':
            replacements['gerbil/compiler/driver'] = (retained.with_suffix('.c'), retained.with_suffix('.o'))
        order = json.loads((root / '.data/d994-parameter-native-trace-profile/module-order.log').read_text().splitlines()[-1])
        modules = [*order, 'gerbil/main']
        sources = [replacements[name][0] if name in replacements else
                   home / 'lib/static' / (name.replace('/', '__') + '.c') for name in modules]
        link = out / 'gerbil-link-original.c'
        run('generate-link', [str(home / 'bin/gsc'), '-link', '-track-scheme', '-o', str(link), *map(str, sources)])
        prior = json.loads((root / '.data/d1083-outlined-inherited-uninstrumented/report.json').read_text())
        selected = {row['module'] for row in prior['objects']}
        paths = [path for path in sources if path.stem.replace('__', '/') in selected]
        if len(paths) != 11:
            raise ValueError('retained outline module closure changed')
        content, details = render(paths, link.read_text(), out,
            guarded_readonly_traces=True, guarded_trace_polls=True,
            guarded_trace_restart_polls=True, guarded_trace_coalesce_polls=True,
            guarded_trace_primitive_boundary=True, guarded_trace_inline_lookup=True,
            guarded_trace_outline_lookup=True, guarded_trace_lookup_return_branches=True,
            parameter_entry_fastpath=True, parameter_identity_return=True,
            parameter_env_lookup=True, bounded_primitive_entries=True,
            guarded_trace_outline_returns=False)
        carrier = out / 'gerbil-link.c'
        carrier.write_text(content)
        objenv.update(BUILD_OBJ_INPUT_FILENAMES_PARAM=str(carrier),
                      BUILD_OBJ_OUTPUT_FILENAME_PARAM=str(out / 'gerbil-link.o'),
                      BUILD_OBJ_META_INFO_FILE_PARAM=str(carrier))
        run('compile-carrier', [str(home / 'bin/gambuild-C'), 'obj'], objenv, budget=900)
        objects = [replacements[name][1] if name in replacements else
                   home / 'lib/static' / (name.replace('/', '__') + '.o') for name in modules]
        run('link-native', [env['CC'], '-o', str(out / 'gerbil'), *map(str, objects),
                           str(out / 'gerbil-link.o'), str(home / 'lib/libgambit.a'), '-ldl', '-lm'])
        (out / 'gxi').symlink_to('gerbil')
        run('smoke', [str(out / 'gxi'), '-e',
            '(import :std/test :std/make) (if (not ' + args.activation +
            ') (error "inactive candidate")) (displayln "IMPORT-OK")'])
        if (out / 'smoke.log').read_text().splitlines()[-1:] != ['IMPORT-OK']:
            raise ValueError('native smoke terminal status')
        report['baselineUnchanged'] = original_hashes == {p: sha(root / p) for p in original_hashes}
        if not report['baselineUnchanged']:
            raise ValueError('frozen inputs changed')
        report.update(qualified=True, binarySha256=sha(out / 'gerbil'), gscSha256=sha(home / 'bin/gsc'))
    finally:
        (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    main()
