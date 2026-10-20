"""Keep the 47s runtime/providers; modify only final Darwin GNU link arguments."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time

from bazel_host_environment import build_environment
from progressive_performance_gate import force_stop
from experiment_framework.patch_lock import verify_patch_lock


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--retain-entry-objects', action='store_true',
                        help='isolated default-off Darwin entry-object cleanup candidate')
    parser.add_argument('--closed-link-driver-library', type=Path,
                        help='merge only the qualified experimental separate compiler definition')
    parser.add_argument('--closed-link-producer-proof', action='store_true')
    parser.add_argument('--closed-link-recipe-proof', action='store_true',
                        help='merge successful-worker recipes into the frozen executor and driver')
    args = parser.parse_args()
    if args.retain_entry_objects and args.closed_link_driver_library:
        parser.error('entry retention must not mix with closed-link experiments')
    if args.closed_link_producer_proof and not args.closed_link_driver_library:
        parser.error('producer proof requires an explicit compiled donor')
    if args.closed_link_recipe_proof and not (args.closed_link_producer_proof and args.closed_link_driver_library):
        parser.error('recipe proof requires producer proof and an explicit compiled donor')
    root = Path(__file__).resolve().parents[3]
    out = args.output.resolve()
    if os.uname().sysname != 'Darwin' or not out.is_relative_to(root / '.data') or out.exists():
        parser.error('fresh isolated Darwin output required')
    stack = root / 'patches/gerbil-v19-darwin'
    verify_patch_lock(stack / 'receipts/d1510-static-c-snapshot-patch-lock.json',
                      root / '.data/d1510-static-c-snapshot-mcp-driver-v1/bin',
                      root / '.data/d1510-reader-whitespace-native-v2', root,
                      root / '.data/d1391-runtime-object-source/build/bin/gsc', True)
    baseline = root / '.data/d1510-reader-whitespace-native-v2'
    receipt = json.loads((baseline / 'report.json').read_text())
    retained = root / '.data/d1510-source-loader-linked'
    original = retained / 'gerbil__compiler__driver.scm'
    original_c = original.with_suffix('.c')
    original_sha = sha(original)
    donor = None
    if args.closed_link_driver_library:
        library = args.closed_link_driver_library.resolve()
        donor = library / 'static/gerbil__compiler__driver.scm'
        if (not library.is_relative_to(root / '.data') or not donor.is_file()
                or donor.is_symlink()):
            parser.error('isolated compiled donor driver required')
    donor_sha = sha(donor) if donor else None
    base_original = root / '.data/d1391-runtime-object-source/build/lib/static/gerbil__compiler__base.scm'
    base_donor = library / 'static/gerbil__compiler__base.scm' if args.closed_link_recipe_proof else None
    if base_donor and (not base_donor.is_file() or base_donor.is_symlink()):
        parser.error('isolated compiled donor base required')
    base_original_sha = sha(base_original) if base_donor else None
    base_donor_sha = sha(base_donor) if base_donor else None
    home = root / '.data/d1391-runtime-object-source/build'
    driver = root / '.data/d1510-shell-substitution/bin'
    env = build_environment()
    env.update(GERBIL_HOME=str(home), GERBIL_LOADPATH=str(home / 'lib'),
               GAMBOPT=f'~~bin={driver},~~lib={home / "lib"},~~include={home / "include"}')
    out.mkdir()
    scm = out / original.name
    local = dict(env, FD_DRIVER_INPUT=str(original), FD_DRIVER_OUTPUT=str(scm))
    if donor:
        local.update(CLOSED_DRIVER_BASE=str(original), CLOSED_DRIVER_DONOR=str(donor),
                     CLOSED_DRIVER_OUTPUT=str(scm),
                     CLOSED_DRIVER_PRODUCER='1' if args.closed_link_producer_proof else '0',
                     CLOSED_DRIVER_RECIPE='1' if args.closed_link_recipe_proof else '0',
                     CLOSED_DRIVER_MODULE='driver')
    report = dict(qualified=False, productionAdmitted=False, performanceQualified=False,
                  scope='frozen-host-private-Darwin-' + ('retained-entry-driver' if args.retain_entry_objects
                        else 'closed-link-driver' if donor else 'final-link-driver'),
                  steps=[])

    def run(name, command, environment=env, budget=120):
        started = time.monotonic()
        with (out / (name + '.log')).open('wb') as log:
            process = subprocess.Popen(command, env=environment, stdout=log, stderr=subprocess.STDOUT,
                                       start_new_session=True)
            try:
                process.wait(timeout=budget)
            finally:
                if process.poll() is None:
                    force_stop(process)
        row = dict(name=name, exitCode=process.returncode, wallSeconds=time.monotonic() - started)
        report['steps'].append(row)
        print(json.dumps(row), flush=True)
        if process.returncode:
            raise RuntimeError(name)

    try:
        transform = Path(__file__).with_name('prepare_closed_link_aot_driver.scm' if donor
                                             else 'prepare_fd_final_driver.scm')
        if args.retain_entry_objects:
            transform = Path(__file__).with_name('prepare_retained_entry_driver.scm')
        run('prepare-driver', [str(baseline / 'gxi'), '-e', '(load ' + json.dumps(str(transform)) + ')'], local)
        cfile, obj = scm.with_suffix('.c'), scm.with_suffix('.o')
        run('generate-driver', [str(driver / 'gsc'), '-c', '-o', str(cfile), str(scm)])
        globals_in = lambda path: set(re.findall(r'^___DEF_GLO\(\d+,(.*)\)$', path.read_text(), re.M))
        original_globals, candidate_globals = globals_in(original_c), globals_in(cfile)
        # DEF_GLO includes imported references, not only module definitions.
        allowed_references = {'"' + name + '"' for name in (
            '##create-temporary-directory', '##list?', '##os-environ', '=',
            'caar', 'cadar', 'caddar', 'caddr', 'delete-directory',
            'string-length', 'string-prefix?',
        )} if donor else set()
        added_references = candidate_globals - original_globals
        if args.closed_link_recipe_proof:
            allowed_references |= {'"gxc#add-compile-output-job!__1"', '"gxc#current-compile-output-recipe"'}
        if original_globals - candidate_globals or added_references != allowed_references:
            raise ValueError('driver global interface changed')
        report['addedImportedReferences'] = sorted(added_references)
        compile_env = dict(env, GAMBITDIR_INCLUDE=str(home / 'include'), GAMBITDIR_LIB=str(home / 'lib'),
                           BUILD_OBJ_INPUT_FILENAMES_PARAM=str(cfile), BUILD_OBJ_OUTPUT_FILENAME_PARAM=str(obj),
                           BUILD_OBJ_META_INFO_FILE_PARAM=str(cfile), BUILD_OBJ_CC_OPTIONS_PARAM='-O1')
        run('compile-driver', [str(driver / 'gambuild-C'), 'obj'], compile_env)
        replacement_objects = {'gerbil/compiler/driver': obj}
        replacement_sources = {'gerbil/compiler/driver': cfile}
        if base_donor:
            base_scm = out / base_original.name
            base_env = dict(local, CLOSED_DRIVER_BASE=str(base_original),
                            CLOSED_DRIVER_DONOR=str(base_donor), CLOSED_DRIVER_OUTPUT=str(base_scm),
                            CLOSED_DRIVER_MODULE='base')
            run('prepare-base', [str(baseline / 'gxi'), '-e', '(load ' + json.dumps(str(transform)) + ')'], base_env)
            base_c, base_obj = base_scm.with_suffix('.c'), base_scm.with_suffix('.o')
            run('generate-base', [str(driver / 'gsc'), '-c', '-o', str(base_c), str(base_scm)])
            old_globals = globals_in(base_original.with_suffix('.c'))
            new_globals = globals_in(base_c)
            expected_added = {'"' + name + '"' for name in (
                'equal?', 'string-copy', 'gxc#add-compile-output-job!__1', 'gxc#current-compile-output-recipe',
            )}
            if old_globals - new_globals or new_globals - old_globals != expected_added:
                raise ValueError('base global interface changed')
            base_compile_env = dict(compile_env, BUILD_OBJ_INPUT_FILENAMES_PARAM=str(base_c),
                                    BUILD_OBJ_OUTPUT_FILENAME_PARAM=str(base_obj),
                                    BUILD_OBJ_META_INFO_FILE_PARAM=str(base_c))
            run('compile-base', [str(driver / 'gambuild-C'), 'obj'], base_compile_env)
            replacement_objects['gerbil/compiler/base'] = base_obj
            replacement_sources['gerbil/compiler/base'] = base_c
            report.update(baseAddedReferences=sorted(expected_added),
                          baseSourceSha256=sha(base_scm), baseObjectSha256=sha(base_obj),
                          frozenBaseSourceSha256=base_original_sha, baseDonorSha256=base_donor_sha)
        order = json.loads((root / '.data/d994-parameter-native-trace-profile/module-order.log').read_text().splitlines()[-1])
        objects = [replacement_objects.get(module, home / 'lib/static' / (module.replace('/', '__') + '.o'))
                   for module in [*order, 'gerbil/main']]
        for index, row in enumerate(receipt['providers']):
            provider = baseline / f'{index}.o'
            if sha(provider) != row['renamedObjectSha256']:
                raise ValueError('frozen provider changed')
        for relative, digest in {**receipt['frozenObjectHashes'], **receipt['privateRuntimeObjects']}.items():
            if sha(root / relative) != digest:
                raise ValueError('frozen native input changed')
        providers = [baseline / f'{index}.o' for index in range(len(receipt['providers']))]
        extra = [root / relative for relative in receipt['privateRuntimeObjects']]
        link_object = retained / 'gerbil-link.o'
        if donor:
            from gambit_host_coalescing import render

            sources = [replacement_sources.get(module, home / 'lib/static' / (module.replace('/', '__') + '.c'))
                       for module in [*order, 'gerbil/main']]
            link_source = out / 'gerbil-link-original.c'
            run('generate-link', [str(driver / 'gsc'), '-link', '-track-scheme',
                                  '-o', str(link_source), *map(str, sources)])
            prior = json.loads((root / '.data/d1083-outlined-inherited-uninstrumented/report.json').read_text())
            selected = {row['module'] for row in prior['objects']}
            paths = [path for path in sources if path.stem.replace('__', '/') in selected]
            if len(paths) != 11 or cfile in paths:
                raise ValueError('frozen coalesced producer selection changed')
            content, details = render(paths, link_source.read_text(), out,
                guarded_readonly_traces=True, guarded_trace_polls=True,
                guarded_trace_restart_polls=True, guarded_trace_coalesce_polls=True,
                guarded_trace_primitive_boundary=True, guarded_trace_inline_lookup=True,
                guarded_trace_outline_lookup=True, guarded_trace_lookup_return_branches=True,
                parameter_entry_fastpath=True, parameter_identity_return=True,
                parameter_env_lookup=True, bounded_primitive_entries=True,
                guarded_trace_outline_returns=False)
            carrier = out / 'gerbil-link.c'
            carrier.write_text(content)
            link_object = out / 'gerbil-link.o'
            carrier_env = dict(compile_env, BUILD_OBJ_INPUT_FILENAMES_PARAM=str(carrier),
                               BUILD_OBJ_OUTPUT_FILENAME_PARAM=str(link_object),
                               BUILD_OBJ_META_INFO_FILE_PARAM=str(carrier))
            run('compile-carrier', [str(driver / 'gambuild-C'), 'obj'], carrier_env, budget=900)
            report['linkObjectSha256'] = sha(link_object)
        run('link-native', [env['CC'], '-o', str(out / 'gerbil'), *map(str, objects),
                           str(link_object), *map(str, providers),
                           str(baseline / 'os_dyn_embedded.o'), *map(str, extra),
                           str(home / 'lib/libgambit.a'), '-ldl', '-lm'])
        (out / 'gxi').symlink_to('gerbil')
        run('smoke', [str(out / 'gxi'), '-e',
                      '(import :std/make :std/test) (displayln "IMPORT-OK")'])
        if ((out / 'smoke.log').read_text().splitlines()[-1:] != ['IMPORT-OK']
                or sha(original) != original_sha or (donor and sha(donor) != donor_sha)
                or (base_donor and (sha(base_original) != base_original_sha or sha(base_donor) != base_donor_sha))):
            raise ValueError('smoke or original source identity failed')
        report.update(qualified=True, sourceUnchanged=True, globalsUnchanged=True,
                      sourceSha256=sha(scm), objectSha256=sha(obj), binarySha256=sha(out / 'gerbil'),
                      gscSha256=sha(driver / 'gsc'), frozenBaselineSha256=sha(baseline / 'gerbil'))
        if donor:
            report.update(donorSha256=donor_sha, frozenDriverSourceSha256=original_sha,
                          transformSha256=sha(transform))
    finally:
        (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    main()
