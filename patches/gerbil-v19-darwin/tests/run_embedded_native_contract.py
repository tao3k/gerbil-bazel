"""Exercise an embedded object-file backend through the real Gambit file API.

The fixture whitelist deliberately lacks production freshness/security admission.
It is never installed or exposed as a default toolchain optimization.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time

from bazel_host_environment import build_environment
from progressive_performance_gate import force_stop
from verify_source_loader_49_baseline import main as verify
from rename_macho_entry import rename_entry


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--rename-entries', action='store_true')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    output = args.output.resolve()
    if os.uname().sysname != 'Darwin' or not output.is_relative_to(root / '.data') or output.exists():
        parser.error('fresh Darwin project-data construction required')
    output.mkdir()
    verify()
    home = root / '.data/d1391-runtime-object-source/build'
    lib = root / '.data/d1391-runtime-object-source/src/gambit/lib'
    driver = root / '.data/d1510-shell-substitution/bin'
    env = build_environment()
    env.update(GAMBOPT=f'~~bin={driver},~~lib={home / "lib"},~~include={home / "include"}',
               EMBEDDED_CONTROL_DIRECTORY=str(output))
    report = dict(qualified=False, performanceAdmitted=False,
                  productionAdmitted=False, renamedEntries=args.rename_entries,
                  scope='embedded-file-backend-prerequisite-only', steps=[])

    def run(name, command, local_env=env, cwd=None):
        started = time.monotonic()
        with (output / (name + '.log')).open('w') as log:
            child = subprocess.Popen(command, env=local_env, cwd=cwd, stdout=log,
                                     stderr=subprocess.STDOUT, start_new_session=True)
            try:
                child.wait(timeout=52)
            finally:
                if child.poll() is None:
                    force_stop(child)
        report['steps'].append(dict(name=name, exitCode=child.returncode,
                                  wallSeconds=time.monotonic() - started))
        print(json.dumps(report['steps'][-1]), flush=True)
        if child.returncode:
            raise RuntimeError(name)

    try:
        fixtures = [('lazy_native_dependency', 'lazy_native_dependency'),
                    ('lazy_native_payload', 'embedded_native_payload'),
                    ('lazy_native_failure', 'lazy_native_failure'),
                    ('embedded_native_fallback', 'embedded_native_fallback'),
                    ('embedded_native_main', 'embedded_native_main')]
        rows = []
        for name, fixture in fixtures:
            source = output / (name + '.scm')
            shutil.copy2(Path(__file__).with_name(fixture + '.scm'), source)
            cfile, obj = source.with_suffix('.c'), source.with_suffix('.o')
            run('generate-' + name, [str(driver / 'gsc'), '-c', '-o', str(cfile), str(source)])
            local = dict(env, GAMBITDIR_INCLUDE=str(home / 'include'), GAMBITDIR_LIB=str(home / 'lib'),
                         BUILD_OBJ_INPUT_FILENAMES_PARAM=str(cfile), BUILD_OBJ_OUTPUT_FILENAME_PARAM=str(obj),
                         BUILD_OBJ_CC_OPTIONS_PARAM='-O1' + (' -D___DYNAMIC' if name != fixtures[-1][0] else ''),
                         BUILD_OBJ_META_INFO_FILE_PARAM=str(cfile))
            run('compile-' + name, [str(driver / 'gambuild-C'), 'obj'], local)
            entry = re.findall(r'^#define ___LINKER_ID (\w+)$', cfile.read_text(), re.M)
            if len(entry) != 1:
                raise ValueError('unique native entry required')
            rows.append(dict(name=name, cfile=cfile, obj=obj, entry=entry[0]))
            if name != fixtures[-1][0]:
                dyn = dict(env, GAMBITDIR_INCLUDE=str(home / 'include'), GAMBITDIR_LIB=str(home / 'lib'),
                           BUILD_DYN_INPUT_FILENAMES_PARAM=str(obj),
                           BUILD_DYN_OUTPUT_FILENAME_PARAM=str(output / (name + '.o1')),
                           BUILD_DYN_META_INFO_FILE_PARAM=str(cfile))
                run('bundle-' + name, [str(driver / 'gambuild-C'), 'dyn'], dyn)
        for index, row in enumerate(rows[:3]):
            row['providerEntry'] = row['entry']
            if args.rename_entries:
                row['providerEntry'] = '___gb_provider_' + str(index)
                renamed = row['obj'].with_name(row['name'] + '-renamed.o')
                renamed.write_bytes(rename_entry(row['obj'].read_bytes(),
                    '_' + row['entry'], '_' + row['providerEntry']))
                row['obj'] = renamed
        declarations = '\n'.join('extern ___mod_or_lnk ' + row['providerEntry'] + '(___global_state);'
                                 for row in rows[:3])
        lookup = '\n'.join(
            '  if (strcmp(cpath, ' + json.dumps(str(output / (row['name'] + '.o1'))) +
            ') == 0 && strcmp(clinkername, ' + json.dumps(row['entry']) + ') == 0) {\n'
            '    *linker = (void*)' + row['providerEntry'] + '; ++gb_provider_hits; return ___FIX(___NO_ERR);\n  }'
            for row in rows[:3])
        original = (lib / 'os_dyn.c').read_text()
        anchor = '  ___SCMOBJ result = ___FIX(___UNIMPL_ERR);'
        if original.count(anchor) != 1:
            raise ValueError('exact dynamic-load hook required')
        guard = '#if defined(__APPLE__) && defined(__MACH__) && defined(__GNUC__) && !defined(__clang__)\n'
        original = original.replace('#include "os_dyn.h"', '#include "os_dyn.h"\n#include <string.h>\n'
                                    'int gb_provider_hits = 0;\nint gb_provider_fallbacks = 0;\n'
                                    + guard + declarations + '\n#endif', 1)
        original = original.replace(anchor, anchor + '\n' + guard + lookup +
                                    '\n  ++gb_provider_fallbacks;\n#endif', 1)
        backend = output / 'os_dyn_embedded.c'
        backend.write_text(original)
        backend_env = dict(local, BUILD_OBJ_INPUT_FILENAMES_PARAM=str(backend),
                           BUILD_OBJ_OUTPUT_FILENAME_PARAM=str(backend.with_suffix('.o')),
                           BUILD_OBJ_META_INFO_FILE_PARAM=str(backend),
                           BUILD_OBJ_CC_OPTIONS_PARAM=(f'-O3 -D___LIBRARY -DHAVE_CONFIG_H '
                                                      f'-I{lib} -I{lib.parent / "include"}'))
        run('compile-embedded-backend', [str(driver / 'gambuild-C'), 'obj'], backend_env)
        link = output / 'embedded_native_link.c'
        run('generate-link', [str(driver / 'gsc'), '-link', '-o', str(link), str(rows[-1]['cfile'])])
        link_env = dict(local, BUILD_OBJ_INPUT_FILENAMES_PARAM=str(link),
                        BUILD_OBJ_OUTPUT_FILENAME_PARAM=str(link.with_suffix('.o')),
                        BUILD_OBJ_META_INFO_FILE_PARAM=str(link), BUILD_OBJ_CC_OPTIONS_PARAM='-O1')
        run('compile-link', [str(driver / 'gambuild-C'), 'obj'], link_env)
        binary = output / 'embedded-native-controls'
        run('link-native', [env['CC'], '-o', str(binary), str(rows[-1]['obj']),
                           *[str(row['obj']) for row in rows[:3]], str(backend.with_suffix('.o')),
                           str(link.with_suffix('.o')), str(home / 'lib/libgambit.a'), '-ldl', '-lm'])
        empty = output / 'empty-working-directory'
        empty.mkdir()
        run('controls', [str(binary)], cwd=empty)
        text = (output / 'controls.log').read_text()
        cases = [line[8:] for line in text.splitlines() if line.startswith('CASE-OK ')]
        if len(cases) != 14 or len(set(cases)) != 14 or text.splitlines()[-1:] != ['OK']:
            raise ValueError('exact native case inventory and final OK required')
        verify()
        report.update(qualified=True, cases=cases, baselineUnchanged=True,
                      binarySha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
                      backendSourceSha256=hashlib.sha256(backend.read_bytes()).hexdigest())
    finally:
        (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
