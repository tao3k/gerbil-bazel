"""Reuse exact retained objects; change only the Darwin native load backend."""
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
from rename_macho_entry import rename_entry
from verify_source_loader_49_baseline import main as verify


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--phi-source-module', action='store_true')
    parser.add_argument('--phi-carrier', type=Path)
    parser.add_argument('--runtime-object', '--raw-eval-object', dest='raw_eval_object', type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    output = args.output.resolve()
    if os.uname().sysname != 'Darwin' or not output.is_relative_to(root / '.data') or output.exists():
        parser.error('fresh isolated Darwin output required')
    verify()
    output.mkdir()
    home = root / '.data/d1391-runtime-object-source/build'
    test_home = root / '.data/d1510-mcp-test-source-home-v2/build'
    lib = root / '.data/d1391-runtime-object-source/src/gambit/lib'
    driver = root / '.data/d1510-shell-substitution/bin'
    retained = root / '.data/d1510-source-loader-linked'
    carrier = retained
    extra_runtime = []
    if args.raw_eval_object:
        obj = args.raw_eval_object.resolve()
        runtime_receipt = json.loads((obj.parent / 'report.json').read_text())
        if not obj.is_relative_to(root / '.data') or not runtime_receipt['qualified'] or sha(obj) != runtime_receipt['objectSha256']:
            raise ValueError('private runtime object provenance mismatch')
        extra_runtime.append(obj)
        link_obj = obj.parent / '_gambit.o'
        if sha(link_obj) != runtime_receipt['runtimeLinkObjectSha256']:
            raise ValueError('private runtime linker object provenance mismatch')
        extra_runtime.append(link_obj)
    if args.phi_source_module:
        carrier = args.phi_carrier.resolve() if args.phi_carrier else root / '.data/d1510-phi-source-native-v2'
        construction = json.loads((carrier / 'report.json').read_text())
        if not carrier.is_relative_to(root / '.data') or not construction['qualified'] or construction['binarySha256'] != sha(carrier / 'gerbil'):
            raise ValueError('phi source construction identity changed')
    captured = root / '.data/d1548-current-active-source-closure'
    source_receipt = json.loads((captured / 'report.json').read_text())
    if not source_receipt['qualified']:
        raise ValueError('native object provenance is not qualified')
    expected = {row['module']: row for row in source_receipt['runs']}
    report = dict(qualified=False, performanceQualified=False, productionAdmitted=False,
                  phiSourceModule=args.phi_source_module,
                  scope='exact-baseline-embedded-provider-construction-only', steps=[], providers=[], excluded=[])
    env = build_environment()
    cores = int(subprocess.check_output(['sysctl', '-n', 'hw.physicalcpu'], text=True))
    env.update(GERBIL_HOME=str(home), GERBIL_LOADPATH=str(home / 'lib'),
               GERBIL_BUILD_CORES=str(cores),
               GAMBOPT=f'~~bin={driver},~~lib={home / "lib"},~~include={home / "include"}')

    def run(name, command, local=env):
        started = time.monotonic()
        with (output / (name + '.log')).open('w') as log:
            child = subprocess.Popen(command, env=local, stdout=log, stderr=subprocess.STDOUT,
                                     start_new_session=True)
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
        declarations, entries, objects = [], [], []
        for directory in sorted(p.parent for p in captured.glob('*/report.json')):
            row = json.loads((directory / 'report.json').read_text())
            original = expected.get(row['module'])
            if original is None or not all(row.get(key) for key in
                    ('passed', 'nativeTextByteExact', 'dependenciesMatch', 'originalUnchanged')):
                raise ValueError('captured native contract changed')
            cfile, obj = directory / 'module.c', directory / 'module.o'
            if sha(cfile) != original['generatedCSha256'] or sha(obj) != original['objectSha256']:
                raise ValueError('captured native bytes changed')
            symbols = re.findall(r'^#define ___LINKER_ID (\w+)$', cfile.read_text(), re.M)
            if len(symbols) != 1:
                raise ValueError('one object entry required')
            old = symbols[0]
            new = '___gb_embedded_provider_' + str(len(objects))
            renamed = output / (str(len(objects)) + '.o')
            try:
                data = rename_entry(obj.read_bytes(), '_' + old, '_' + new)
            except ValueError as error:
                report['excluded'].append(dict(module=row['module'], reason=str(error)))
                continue
            renamed.write_bytes(data)
            native = home / row['activePath']
            digest = sha(native)
            declarations.append('extern ___mod_or_lnk ' + new + '(___global_state);')
            paths = [native, test_home / row['activePath']]
            for path in paths:
                entries.append('{ ' + json.dumps(str(path)) + ', ' + json.dumps(old) + ', ' +
                               json.dumps(digest) + ', (void*)' + new + ' }')
            objects.append(renamed)
            report['providers'].append(dict(module=row['module'], activePath=row['activePath'],
                originalObjectSha256=sha(obj), originalImageSha256=digest, renamedObjectSha256=sha(renamed)))
        if not objects:
            raise ValueError('no eligible ordinary native providers')
        guard = '#if defined(__APPLE__) && defined(__MACH__) && defined(__GNUC__) && !defined(__clang__)\n'
        preamble = guard + '''#include <CommonCrypto/CommonDigest.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
''' + '\n'.join(declarations) + '''
typedef struct { const char *path; const char *name; const char *sha; void *entry; } gb_provider;
static const gb_provider gb_providers[] = {
''' + ',\n'.join(entries) + '''
};
static unsigned gb_hits, gb_misses;
static int gb_reporting;
static void gb_report(void) {
  const char *prefix = getenv("GB_EMBEDDED_STATS");
  char path[4096]; FILE *out;
  if (!prefix || snprintf(path, sizeof(path), "%s.%ld.json", prefix, (long)getpid()) >= sizeof(path)) return;
  out = fopen(path, "w");
  if (out) { fprintf(out, "{\\\"hits\\\":%u,\\\"misses\\\":%u}\\n", gb_hits, gb_misses); fclose(out); }
}
static int gb_matches(const char *path, const char *expected) {
  unsigned char buffer[65536], digest[CC_SHA256_DIGEST_LENGTH]; char encoded[65];
  CC_SHA256_CTX context; size_t n, i; FILE *file = fopen(path, "rb");
  if (!file) return 0;
  CC_SHA256_Init(&context);
  while ((n = fread(buffer, 1, sizeof(buffer), file)) != 0) CC_SHA256_Update(&context, buffer, (CC_LONG)n);
  if (ferror(file)) { fclose(file); return 0; }
  fclose(file); CC_SHA256_Final(digest, &context);
  for (i = 0; i < sizeof(digest); ++i) sprintf(encoded + 2*i, "%02x", digest[i]);
  return strcmp(encoded, expected) == 0;
}
static void *gb_find_provider(const char *path, const char *name) {
  size_t i;
  if (!gb_reporting && getenv("GB_EMBEDDED_STATS")) { atexit(gb_report); gb_reporting = 1; }
  for (i = 0; i < sizeof(gb_providers)/sizeof(gb_providers[0]); ++i) {
    const gb_provider *p = &gb_providers[i];
    if (strcmp(path, p->path) == 0 && strcmp(name, p->name) == 0 && gb_matches(path, p->sha)) {
      ++gb_hits; return p->entry;
    }
  }
  ++gb_misses; return 0;
}
#endif
'''
        original = (lib / 'os_dyn.c').read_text()
        original = original.replace('#include "os_dyn.h"', '#include "os_dyn.h"\n' + preamble, 1)
        anchor = '  ___SCMOBJ result = ___FIX(___UNIMPL_ERR);'
        if original.count(anchor) != 1:
            raise ValueError('exact dynamic-load hook required')
        original = original.replace(anchor, anchor + '\n' + guard +
            '  void *embedded = gb_find_provider(cpath, clinkername);\n'
            '  if (embedded) { *linker = embedded; return ___FIX(___NO_ERR); }\n#endif', 1)
        backend = output / 'os_dyn_embedded.c'
        backend.write_text(original)
        local = dict(env, GAMBITDIR_INCLUDE=str(home / 'include'), GAMBITDIR_LIB=str(home / 'lib'),
                     BUILD_OBJ_INPUT_FILENAMES_PARAM=str(backend),
                     BUILD_OBJ_OUTPUT_FILENAME_PARAM=str(backend.with_suffix('.o')),
                     BUILD_OBJ_META_INFO_FILE_PARAM=str(backend),
                     BUILD_OBJ_CC_OPTIONS_PARAM=f'-O3 -D___LIBRARY -DHAVE_CONFIG_H -I{lib} -I{lib.parent / "include"}')
        run('compile-embedded-backend', [str(driver / 'gambuild-C'), 'obj'], local)
        order = json.loads((root / '.data/d994-parameter-native-trace-profile/module-order.log').read_text().splitlines()[-1])
        baseline_objects = [carrier / 'gerbil__compiler__driver.o' if name == 'gerbil/compiler/driver'
                            else home / 'lib/static' / (name.replace('/', '__') + '.o')
                            for name in [*order, 'gerbil/main']]
        frozen_objects = {str(path.relative_to(root)): sha(path) for path in
                          [*baseline_objects, carrier / 'gerbil-link.o', home / 'lib/libgambit.a']}
        run('link-native', [env['CC'], '-o', str(output / 'gerbil'), *map(str, baseline_objects),
                           str(carrier / 'gerbil-link.o'), *map(str, objects), str(backend.with_suffix('.o')),
                           *map(str, extra_runtime),
                           str(home / 'lib/libgambit.a'), '-ldl', '-lm'])
        (output / 'gxi').symlink_to('gerbil')
        smoke_env = dict(env, GB_EMBEDDED_STATS=str(output / 'smoke-native'))
        run('smoke', [str(output / 'gxi'), '-e', '(import :std/make :std/test) (displayln "IMPORT-OK")'], smoke_env)
        stats = [json.loads(path.read_text()) for path in output.glob('smoke-native.*.json')]
        if (output / 'smoke.log').read_text().splitlines()[-1:] != ['IMPORT-OK'] or len(stats) != 1 or stats[0]['hits'] <= 0:
            raise ValueError('actual native provider coverage or import smoke failed')
        verify()
        if frozen_objects != {relative: sha(root / relative) for relative in frozen_objects}:
            raise ValueError('original native objects changed')
        report.update(qualified=True, baselineUnchanged=True, cores=cores,
                      privateRuntimeObjects={str(path.relative_to(root)): sha(path) for path in extra_runtime},
                      frozenObjectHashes=frozen_objects, smokeCoverage=stats[0],
                      binarySha256=sha(output / 'gerbil'), gscSha256=sha(driver / 'gsc'))
    finally:
        (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
