"""Extend the retained experimental native-provider host with verified objects."""
import argparse
import json
from pathlib import Path
import re
import subprocess

from bazel_host_environment import build_environment
from native_object_manifest import digest
from probe_retained_native_loader import FROZEN, replace_once
from rename_macho_entry import rename_entry
from run_parser_native_admission_cost import run
from run_stdlib_import_cost import parse_inventory, parse_phases


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capture', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    capture, output = args.capture.resolve(), args.output.resolve()
    if output.exists() or not all(p.is_relative_to(root / '.data') for p in (capture, output)):
        parser.error('persistent capture and fresh .data output required')
    retained = root / '.data/d1510-reader-whitespace-native-v2'
    manifest = json.loads((retained / 'report.json').read_text())
    captured = json.loads((capture / 'report.json').read_text())
    if (not manifest['qualified'] or digest(retained / 'gerbil') != FROZEN
            or not captured['qualified'] or not captured['inputsUnchanged']):
        raise ValueError('unchanged retained host and qualified capture required')
    home = root / '.data/d1391-runtime-object-source/build'
    test_home = root / '.data/d1510-mcp-test-source-home-v2/build'
    locked = {**manifest['frozenObjectHashes'], **manifest['privateRuntimeObjects']}
    if any(digest(root / path) != expected for path, expected in locked.items()):
        raise ValueError('retained objects changed')
    if any(digest(home / path) != expected for path, expected in captured['inputHashes'].items()):
        raise ValueError('captured original inputs changed')
    env = build_environment()
    cores = int(subprocess.check_output(['sysctl', '-n', 'hw.physicalcpu'], text=True))
    env['GERBIL_BUILD_CORES'] = str(cores)
    output.mkdir()
    report = dict(scope='retained-provider-extension-pilot-not-release-admission',
                  qualified=False, performanceQualified=False, productionAdmitted=False,
                  retainedBinarySha256=FROZEN, captureReceiptSha256=digest(capture / 'report.json'),
                  hardwareWorkers=cores, extensions=[], steps=[], runs=[])
    try:
        declarations, entries, extra_objects = [], [], []
        capture_rows = {row['module']: row for row in captured['runs']}
        for folder in sorted(capture.glob('*/report.json')):
            row = json.loads(folder.read_text())
            if row != capture_rows.get(row['module']) or not row['passed']:
                raise ValueError('individual capture receipt changed')
            cfile, obj = folder.parent / 'module.c', folder.parent / 'module.o'
            if digest(cfile) != row['generatedCSha256'] or digest(obj) != row['objectSha256']:
                raise ValueError('captured bytes changed')
            names = re.findall(r'^#define ___LINKER_ID (\w+)$', cfile.read_text(), re.M)
            if len(names) != 1:
                raise ValueError('one ordinary module linker required')
            old, new = names[0], '___gb_extension_' + str(len(extra_objects))
            renamed = output / (str(len(extra_objects)) + '.o')
            renamed.write_bytes(rename_entry(obj.read_bytes(), '_' + old, '_' + new))
            extra_objects.append(renamed)
            image = home / row['activePath']
            declarations.append('extern ___mod_or_lnk ' + new + '(___global_state);')
            for path in (image, test_home / row['activePath']):
                if digest(path) != captured['inputHashes'][row['activePath']]:
                    raise ValueError('provider alias image identity differs')
                entries.append('{ ' + json.dumps(str(path)) + ', ' + json.dumps(old) + ', ' +
                               json.dumps(digest(path)) + ', (void*)' + new + ' }')
            report['extensions'].append(dict(module=row['module'], linker=old,
                activePath=row['activePath'], renamedObjectSha256=digest(renamed)))
        if not extra_objects:
            raise ValueError('nonempty extension required')
        source = (retained / 'os_dyn_embedded.c').read_text()
        source = replace_once(source, 'typedef struct { const char *path;',
                              '\n'.join(declarations) + '\ntypedef struct { const char *path;')
        source = replace_once(source, 'static const gb_provider gb_providers[] = {\n',
                              'static const gb_provider gb_providers[] = {\n' + ',\n'.join(entries) + ',\n')
        source = replace_once(source, '      ++gb_hits; return p->entry;',
                              f'      if (i < {len(entries)} && getenv("GB_PROVIDER_EXTENSION_TRACE"))\n'
                              '        fprintf(stderr, "EXTENSION-HIT\\t%s\\n", p->name);\n'
                              '      ++gb_hits; return p->entry;')
        cfile = output / 'os_dyn_extended.c'
        cfile.write_text(source)
        lib = root / '.data/d1391-runtime-object-source/src/gambit/lib'
        driver = root / '.data/d1510-shell-substitution/bin/gambuild-C'
        local = dict(env, GERBIL_HOME=str(home), GAMBITDIR_INCLUDE=str(home / 'include'),
                     GAMBITDIR_LIB=str(home / 'lib'), BUILD_OBJ_INPUT_FILENAMES_PARAM=str(cfile),
                     BUILD_OBJ_OUTPUT_FILENAME_PARAM=str(cfile.with_suffix('.o')),
                     BUILD_OBJ_META_INFO_FILE_PARAM=str(cfile),
                     BUILD_OBJ_CC_OPTIONS_PARAM=f'-O3 -D___LIBRARY -DHAVE_CONFIG_H -I{lib} -I{lib.parent / "include"}')
        report['steps'].append(run([str(driver), 'obj'], output, local, output / 'compile.log', 50))
        providers = [retained / f'{index}.o' for index in range(len(manifest['providers']))]
        if any(digest(path) != row['renamedObjectSha256'] for path, row in zip(providers, manifest['providers'])):
            raise ValueError('original provider bytes changed')
        objects = [root / path for path in manifest['frozenObjectHashes'] if not path.endswith('libgambit.a')]
        report['steps'].append(run([env['CC'], '-o', str(output / 'gerbil'), *map(str, objects),
            *map(str, providers), *map(str, extra_objects), str(cfile.with_suffix('.o')),
            *map(str, (root / path for path in manifest['privateRuntimeObjects'])),
            str(home / 'lib/libgambit.a'), '-ldl', '-lm'], output, env, output / 'link.log', 50))
        report['binarySha256'] = digest(output / 'gerbil')
        (output / 'gxi').symlink_to('gerbil')
        (output / 'control').mkdir()
        (output / 'control/gxi').symlink_to(retained / 'gerbil')
        (output / 'package-home').mkdir()
        for key in tuple(env):
            if key.startswith(('GAMBIT_DARWIN_', 'GERBIL_MCP_')):
                env.pop(key)
        env.pop('GERBIL_BUILD_PREFIX', None)
        env.update(GERBIL_HOME=str(test_home), GERBIL_PATH=str(output / 'package-home'),
                   GERBIL_LOADPATH=str(test_home / 'lib'), GAMBIT_EMBEDDED_NATIVE='0',
                   GB_PROVIDER_EXTENSION_TRACE='1')
        fixture = Path(__file__).with_name('stdlib_import_cost.scm')
        for index, module in enumerate((':std/make', ':std/test', ':std/encoding/json', ':std/list/list')):
            pair = []
            for role, binary in (('control', output / 'control/gxi'), ('candidate', output / 'gxi')):
                log = output / f'{index}-{role}.log'
                row = run([str(binary), '-e', '(begin (load ' + json.dumps(str(fixture)) +
                           ") (stdlib-import-cost '" + module + '))'], output, env, log, 20)
                text = log.read_text()
                row.update(role=role, module=module, phases=parse_phases(text), inventory=parse_inventory(text),
                           extensionHits=[line.split('\t', 1)[1] for line in text.splitlines()
                                          if line.startswith('EXTENSION-HIT\t')])
                report['runs'].append(row)
                pair.append(row)
            if pair[0]['inventory'] != pair[1]['inventory'] or pair[0]['extensionHits']:
                raise ValueError('original inventories differ or control reaches extension')
        hits = {hit for row in report['runs'] for hit in row['extensionHits']}
        if hits != {row['linker'] for row in report['extensions']}:
            raise ValueError('every added provider must actually be reached')
        report['baselineUnchanged'] = (digest(retained / 'gerbil') == FROZEN and
            all(digest(root / path) == expected for path, expected in locked.items()) and
            all(digest(home / path) == expected for path, expected in captured['inputHashes'].items()))
        report['qualified'] = report['baselineUnchanged']
    except Exception as error:
        report['failure'] = repr(error)
    (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({key: value for key, value in report.items() if key != 'runs'}), flush=True)
    return 0 if report['qualified'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
