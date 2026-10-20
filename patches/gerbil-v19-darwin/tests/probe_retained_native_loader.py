"""Relink the retained host with diagnostic-only native loader boundaries."""
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
from run_stdlib_import_cost import parse_inventory, parse_phases, parse_budgets


FROZEN = '1f83878a01744817ceb6e74e5d07138948930a41386e568d156210ce9108bb21'
INITIAL_PHASES = ('osAndMemory', 'initialLinker', 'symbolsAndGlobals1',
                  'symbolsAndGlobals2', 'initialModules')
DYNAMIC_PHASES = ('fixup', 'undefinedGlobals', 'descriptorsAndCSetup')
FIXUP_PHASES = ('globalNames', 'symbolKeywordNames', 'objectReferences', 'labelsAndFrames')
CPU_BOUNDARIES = ('digest', 'dlopen', 'setup', 'linker')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replace_once(source, old, new):
    if source.count(old) != 1:
        raise ValueError('retained loader anchor changed: ' + old[:60])
    return source.replace(old, new, 1)


def instrument(source):
    source = replace_once(source, 'static int gb_matches(', 'static int gb_matches_original(')
    source = replace_once(source, 'static void *gb_find_provider(', '''
#include <time.h>
static unsigned long long gb_digest_ns, gb_provider_ns, gb_dlopen_ns;
static unsigned gb_digest_calls, gb_provider_calls, gb_dlopen_calls;
static unsigned long long gb_setup_ns, gb_linker_ns;
static unsigned gb_setup_calls, gb_linker_calls;
static unsigned long long gb_now(void) {
  struct timespec t;
  if (clock_gettime(CLOCK_MONOTONIC, &t) != 0) abort();
  return (unsigned long long)t.tv_sec * 1000000000ULL + t.tv_nsec;
}
unsigned long long gb_loader_now(void) { return gb_now(); }
void gb_loader_setup_time(unsigned long long ns) {
  __atomic_fetch_add(&gb_setup_ns, ns, __ATOMIC_RELAXED);
  __atomic_fetch_add(&gb_setup_calls, 1, __ATOMIC_RELAXED);
}
void gb_loader_linker_time(unsigned long long ns) {
  __atomic_fetch_add(&gb_linker_ns, ns, __ATOMIC_RELAXED);
  __atomic_fetch_add(&gb_linker_calls, 1, __ATOMIC_RELAXED);
}
static int gb_matches(const char *path, const char *expected) {
  unsigned long long start = gb_now();
  int result = gb_matches_original(path, expected);
  __atomic_fetch_add(&gb_digest_ns, gb_now() - start, __ATOMIC_RELAXED);
  __atomic_fetch_add(&gb_digest_calls, 1, __ATOMIC_RELAXED);
  return result;
}
static void *gb_find_provider_original(''')
    source = replace_once(source, '  ++gb_misses; return 0;\n}\n#endif', '''  ++gb_misses; return 0;
}
static void gb_loader_report(void) {
  const char *prefix = getenv("GB_LOADER_STATS");
  char path[4096];
  FILE *out;
  if (!prefix || snprintf(path, sizeof(path), "%s.%ld.json", prefix, (long)getpid()) >= sizeof(path)
      || !(out = fopen(path, "w"))) return;
  fprintf(out, "{\\"digestNs\\":%llu,\\"providerNs\\":%llu,\\"dlopenNs\\":%llu,"
               "\\"digestCalls\\":%u,\\"providerCalls\\":%u,\\"dlopenCalls\\":%u,"
               "\\"setupNs\\":%llu,\\"linkerNs\\":%llu,\\"setupCalls\\":%u,\\"linkerCalls\\":%u}\\n",
          gb_digest_ns, gb_provider_ns, gb_dlopen_ns,
          gb_digest_calls, gb_provider_calls, gb_dlopen_calls,
          gb_setup_ns, gb_linker_ns, gb_setup_calls, gb_linker_calls);
  fclose(out);
}
static void *gb_find_provider(const char *path, const char *name) {
  static int reporting;
  unsigned long long start;
  void *result;
  if (!reporting) { atexit(gb_loader_report); reporting = 1; }
  start = gb_now();
  result = gb_find_provider_original(path, name);
  __atomic_fetch_add(&gb_provider_ns, gb_now() - start, __ATOMIC_RELAXED);
  __atomic_fetch_add(&gb_provider_calls, 1, __ATOMIC_RELAXED);
  return result;
}
#ifdef USE_dlopen
static void *gb_dlopen(const char *path, int mode) {
  unsigned long long start = gb_now();
  void *result = dlopen(path, mode);
  __atomic_fetch_add(&gb_dlopen_ns, gb_now() - start, __ATOMIC_RELAXED);
  __atomic_fetch_add(&gb_dlopen_calls, 1, __ATOMIC_RELAXED);
  return result;
}
#endif
#endif''')
    for mode in ('RTLD_NOW', '1'):
        source = replace_once(source, f'p->descr = dlopen (cpath, {mode});',
                              f'p->descr = gb_dlopen (cpath, {mode});')
    return source


def instrument_setup(source, initial=False):
    source = replace_once(source, '#include "setup.h"', '''#include "setup.h"
extern unsigned long long gb_loader_now(void);
extern void gb_loader_setup_time(unsigned long long ns);
extern void gb_loader_linker_time(unsigned long long ns);''')
    source = replace_once(source, '''      mol = linker_to_mod_or_lnk
              (___CAST(___mod_or_lnk (*) ___P((___global_state),()),
                       linker));''', '''      {
        unsigned long long start = gb_loader_now();
        mol = linker_to_mod_or_lnk
                (___CAST(___mod_or_lnk (*) ___P((___global_state),()),
                         linker));
        gb_loader_linker_time(gb_loader_now() - start);
      }''')
    source = replace_once(source, '          result = setup_modules (___PSTATE, mol, 1);', '''          {
            unsigned long long start = gb_loader_now();
            result = setup_modules (___PSTATE, mol, 1);
            gb_loader_setup_time(gb_loader_now() - start);
          }''')
    if not initial:
        return source
    declarations = '''
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
static unsigned long long gb_initial_ns[5];
static unsigned long long gb_initial_started;
static unsigned gb_initial_calls[5];
static void gb_initial_report(void) {
  unsigned long long finished = gb_loader_now();
  const char *prefix = getenv("GB_INITIAL_SETUP_STATS");
  char path[4096];
  FILE *out;
  unsigned i;
  if (!prefix || snprintf(path, sizeof(path), "%s.%ld.json", prefix, (long)getpid()) >= sizeof(path)
      || !(out = fopen(path, "w"))) return;
  fprintf(out, "{\\"startedNs\\":%llu,\\"finishedNs\\":%llu,\\"nanoseconds\\":[",
          gb_initial_started, finished);
  for (i = 0; i < 5; ++i) fprintf(out, "%s%llu", i ? "," : "", gb_initial_ns[i]);
  fputs("],\\"calls\\":[", out);
  for (i = 0; i < 5; ++i) fprintf(out, "%s%u", i ? "," : "", gb_initial_calls[i]);
  fputs("]}\\n", out);
  fclose(out);
}
static unsigned long long gb_initial_begin(void) {
  static int reporting;
  unsigned long long now = gb_loader_now();
  if (!reporting) {
    gb_initial_started = now;
    atexit(gb_initial_report);
    reporting = 1;
  }
  return now;
}
static void gb_initial_end(unsigned phase, unsigned long long start) {
  gb_initial_ns[phase] += gb_loader_now() - start;
  ++gb_initial_calls[phase];
}
'''
    source = replace_once(source, 'extern void gb_loader_linker_time(unsigned long long ns);',
                          'extern void gb_loader_linker_time(unsigned long long ns);' + declarations)
    anchors = (
        '  if ((err = setup_os_and_mem ()) != ___FIX(___NO_ERR))\n    return err;',
        '  mol = linker_to_mod_or_lnk (___GSTATE->setup_params.linker);',
        '  init_symkey_glo1 (mol);',
        '  init_symkey_glo2 (mol);',
        '      err = setup_modules (___ps, mol, 0);',
    )
    for index, expression in enumerate(anchors):
        source = replace_once(source, expression, '\n'.join((
            '  {', '    unsigned long long start = gb_initial_begin();', expression,
            f'    gb_initial_end({index}, start);', '  }')))
    return source


def instrument_dynamic_walks(source):
    declarations = r'''
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
static unsigned long long gb_dynamic_ns[3];
static unsigned gb_dynamic_calls[3];
static void gb_dynamic_report(void) {
  const char *prefix = getenv("GB_DYNAMIC_SETUP_STATS");
  char path[4096];
  FILE *out;
  unsigned i;
  if (!prefix || snprintf(path, sizeof(path), "%s.%ld.json", prefix, (long)getpid()) >= sizeof(path)
      || !(out = fopen(path, "w"))) return;
  fputs("{\"nanoseconds\":[", out);
  for (i = 0; i < 3; ++i) fprintf(out, "%s%llu", i ? "," : "", gb_dynamic_ns[i]);
  fputs("],\"calls\":[", out);
  for (i = 0; i < 3; ++i) fprintf(out, "%s%u", i ? "," : "", gb_dynamic_calls[i]);
  fputs("]}\n", out);
  fclose(out);
}
static ___SCMOBJ gb_dynamic_walk(fem_context *ctx, ___mod_or_lnk mol,
  ___SCMOBJ (*proc)(fem_context*, ___module_struct*), unsigned phase) {
  static int reporting;
  unsigned long long start;
  ___SCMOBJ result;
  if (!ctx->collect_undef_glo) return for_each_module(ctx, mol, proc);
  if (!reporting) { atexit(gb_dynamic_report); reporting = 1; }
  start = gb_loader_now();
  result = for_each_module(ctx, mol, proc);
  gb_dynamic_ns[phase] += gb_loader_now() - start;
  ++gb_dynamic_calls[phase];
  return result;
}
'''
    source = replace_once(source, '___HIDDEN ___SCMOBJ setup_modules\n',
                          declarations + '\n___HIDDEN ___SCMOBJ setup_modules\n')
    for index, (spaces, callback) in enumerate((
            (33, 'setup_module_fixup'), (37, 'setup_module_collect_undef_globals'),
            (33, 'setup_module_collect_moddescrs'))):
        original = 'for_each_module (ctx,\n' + ' ' * spaces + 'mol,\n' + \
                   ' ' * spaces + callback + ')'
        source = replace_once(source, original,
            f'gb_dynamic_walk (ctx, mol, {callback}, {index})')
    return source


def parse_dynamic_stats(row, loader):
    if (set(row) != {'nanoseconds', 'calls'} or len(row['nanoseconds']) != 3
            or len(row['calls']) != 3
            or any(type(value) is not int or value < 0 for value in row['nanoseconds'])
            or any(type(value) is not int or value != loader['setupCalls'] for value in row['calls'])
            or loader['setupCalls'] <= 0):
        raise ValueError('each dynamic setup pass must complete once per original setup')
    total = sum(row['nanoseconds'])
    if total > loader['setupNs']:
        raise ValueError('dynamic passes must remain inside original setup interval')
    return dict(zip(DYNAMIC_PHASES, row['nanoseconds']), totalObservedNs=total,
                residualSetupNs=loader['setupNs'] - total, calls=loader['setupCalls'])


def instrument_fixup_detail(source):
    declarations = r'''
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
static unsigned long long gb_fixup_ns[4];
static unsigned gb_fixup_calls[4];
static void gb_fixup_report(void) {
  const char *prefix = getenv("GB_FIXUP_STATS");
  char path[4096];
  FILE *out;
  unsigned i;
  if (!prefix || snprintf(path, sizeof(path), "%s.%ld.json", prefix, (long)getpid()) >= sizeof(path)
      || !(out = fopen(path, "w"))) return;
  fputs("{\"nanoseconds\":[", out);
  for (i = 0; i < 4; ++i) fprintf(out, "%s%llu", i ? "," : "", gb_fixup_ns[i]);
  fputs("],\"calls\":[", out);
  for (i = 0; i < 4; ++i) fprintf(out, "%s%u", i ? "," : "", gb_fixup_calls[i]);
  fputs("]}\n", out);
  fclose(out);
}
static unsigned long long gb_fixup_begin(int dynamic) {
  static int reporting;
  if (!dynamic) return 0;
  if (!reporting) { atexit(gb_fixup_report); reporting = 1; }
  return gb_loader_now();
}
static void gb_fixup_end(unsigned phase, unsigned long long start) {
  if (!start) return;
  gb_fixup_ns[phase] += gb_loader_now() - start;
  ++gb_fixup_calls[phase];
}
'''
    begin = '___HIDDEN ___SCMOBJ setup_module_fixup\n'
    end = '___HIDDEN ___SCMOBJ setup_module_collect_undef_globals\n'
    if source.count(begin) != 1 or source.count(end) != 1:
        raise ValueError('exact original fixup boundaries required')
    first, last = source.index(begin), source.index(end)
    body = replace_once(source[first:last], '  ___WORD ___temp;',
                        '  ___WORD ___temp;\n  unsigned long long gb_fixup_start;')
    markers = ("  /* Setup module's global variable table */",
               "  /* Setup module's symbol table */",
               "  /* Setup module's subtyped object table */",
               "  /* Align module's out-of-line frame descriptor table */")
    for index, marker in enumerate(markers):
        prefix = '' if index == 0 else f'  gb_fixup_end({index - 1}, gb_fixup_start);\n'
        body = replace_once(body, marker,
            prefix + '  gb_fixup_start = gb_fixup_begin(ctx->collect_undef_glo);\n' + marker)
    body = replace_once(body, '  return ___FIX(___NO_ERR);\n}',
        '  gb_fixup_end(3, gb_fixup_start);\n  return ___FIX(___NO_ERR);\n}')
    return source[:first] + declarations + '\n' + body + source[last:]


def instrument_loader_cpu(loader, setup):
    helpers = '''
#include <sys/resource.h>
static unsigned long long gb_cpu_totals[4][4];
static unsigned gb_cpu_calls[4];
static int gb_cpu_active;
static char gb_cpu_prefix[4096], gb_wall_prefix[4096];
static void gb_cpu_capture_prefixes(void) {
  const char *cpu = getenv("GB_LOADER_CPU_STATS"), *wall = getenv("GB_LOADER_STATS");
  if (snprintf(gb_cpu_prefix, sizeof(gb_cpu_prefix), "%s", cpu ? cpu : "") >= sizeof(gb_cpu_prefix)
      || snprintf(gb_wall_prefix, sizeof(gb_wall_prefix), "%s", wall ? wall : "") >= sizeof(gb_wall_prefix)) abort();
}
static void gb_cpu_enable(void) {
  const char *enabled;
  if (gb_cpu_active || !(enabled = getenv("GB_LOADER_OBSERVE")) || strcmp(enabled, "1")) return;
  memset(gb_cpu_totals, 0, sizeof(gb_cpu_totals));
  memset(gb_cpu_calls, 0, sizeof(gb_cpu_calls));
  gb_digest_ns = gb_provider_ns = gb_dlopen_ns = gb_setup_ns = gb_linker_ns = 0;
  gb_digest_calls = gb_provider_calls = gb_dlopen_calls = gb_setup_calls = gb_linker_calls = 0;
  gb_cpu_active = 1;
}
void gb_loader_cpu_begin(unsigned long long values[4]) {
  struct rusage r;
  if (getrusage(RUSAGE_SELF, &r) != 0) abort();
  values[0] = (unsigned long long)r.ru_utime.tv_sec * 1000000ULL + r.ru_utime.tv_usec;
  values[1] = (unsigned long long)r.ru_stime.tv_sec * 1000000ULL + r.ru_stime.tv_usec;
  values[2] = r.ru_minflt;
  values[3] = r.ru_majflt;
}
void gb_loader_cpu_end(unsigned index, const unsigned long long before[4]) {
  unsigned long long after[4]; unsigned i;
  gb_loader_cpu_begin(after);
  for (i = 0; i < 4; ++i) {
    if (after[i] < before[i]) abort();
    __atomic_fetch_add(&gb_cpu_totals[index][i], after[i] - before[i], __ATOMIC_RELAXED);
  }
  __atomic_fetch_add(&gb_cpu_calls[index], 1, __ATOMIC_RELAXED);
}
static void gb_cpu_report(void) {
  const char *prefix = gb_cpu_prefix;
  char path[4096]; FILE *out; unsigned i, j;
  if (!*prefix || snprintf(path, sizeof(path), "%s.%ld.json", prefix, (long)getpid()) >= sizeof(path)
      || !(out = fopen(path, "w"))) return;
  fputs("{\\"totals\\":[", out);
  for (i = 0; i < 4; ++i) {
    fprintf(out, "%s[", i ? "," : "");
    for (j = 0; j < 4; ++j) fprintf(out, "%s%llu", j ? "," : "", gb_cpu_totals[i][j]);
    fputc(']', out);
  }
  fputs("],\\"calls\\":[", out);
  for (i = 0; i < 4; ++i) fprintf(out, "%s%u", i ? "," : "", gb_cpu_calls[i]);
  fputs("]}\\n", out); fclose(out);
}
'''
    loader = replace_once(loader, 'static int gb_matches(const char *path, const char *expected) {',
        helpers + '\nstatic int gb_matches(const char *path, const char *expected) {')
    for index, call in enumerate(('int result = gb_matches_original(path, expected);',
                                  'void *result = dlopen(path, mode);')):
        loader = replace_once(loader, '  ' + call,
            '  unsigned long long cpu_before[4];\n  gb_loader_cpu_begin(cpu_before);\n'
            '  ' + call + f'\n  gb_loader_cpu_end({index}, cpu_before);')
    loader = replace_once(loader, 'atexit(gb_loader_report);',
                          'gb_cpu_capture_prefixes(); atexit(gb_loader_report); atexit(gb_cpu_report);')
    loader = replace_once(loader, 'const char *prefix = getenv("GB_LOADER_STATS");',
                          'const char *prefix = gb_wall_prefix;')
    loader = replace_once(loader, '  start = gb_now();\n  result = gb_find_provider_original',
                          '  gb_cpu_enable();\n  start = gb_now();\n  result = gb_find_provider_original')
    setup = replace_once(setup, 'extern unsigned long long gb_loader_now(void);',
        'extern unsigned long long gb_loader_now(void);\n'
        'extern void gb_loader_cpu_begin(unsigned long long values[4]);\n'
        'extern void gb_loader_cpu_end(unsigned index, const unsigned long long before[4]);')
    for index, call in ((2, 'gb_loader_setup_time'), (3, 'gb_loader_linker_time')):
        # Original calls and result/error handling remain inside the existing intervals.
        anchor = call + '(gb_loader_now() - start);'
        pos = setup.index(anchor)
        start = setup.rfind('unsigned long long start = gb_loader_now();', 0, pos)
        if start < 0:
            raise ValueError('containing setup interval required')
        setup = setup[:start] + setup[start:].replace(
            'unsigned long long start = gb_loader_now();',
            'unsigned long long start = gb_loader_now();\n'
            '            unsigned long long cpu_before[4];\n'
            '            gb_loader_cpu_begin(cpu_before);', 1)
        setup = replace_once(setup, anchor,
            f'gb_loader_cpu_end({index}, cpu_before);\n            ' + anchor)
    return loader, setup


def parse_cpu_stats(row, loader):
    if (set(row) != {'totals', 'calls'} or len(row['totals']) != 4 or len(row['calls']) != 4
            or any(not isinstance(values, list) or len(values) != 4
                   or any(type(value) is not int or value < 0 for value in values)
                   for values in row['totals'])
            or any(type(value) is not int or value < 0 for value in row['calls'])):
        raise ValueError('complete loader CPU and fault counters required')
    result = {}
    for name, values, calls in zip(CPU_BOUNDARIES, row['totals'], row['calls']):
        if calls != loader[name + 'Calls'] or (not calls and any(values)):
            raise ValueError('CPU observations must match completed loader calls')
        result[name] = dict(zip(('userMicroseconds', 'systemMicroseconds',
                                 'minorFaults', 'majorFaults'), values), calls=calls)
    return result


def parse_fixup_stats(row, dynamic):
    if (set(row) != {'nanoseconds', 'calls'} or len(row['nanoseconds']) != 4
            or len(row['calls']) != 4
            or any(type(value) is not int or value < 0 for value in row['nanoseconds'])
            or any(type(value) is not int or value <= 0 for value in row['calls'])
            or len(set(row['calls'])) != 1):
        raise ValueError('all four fixup segments must finish per observed module')
    total = sum(row['nanoseconds'])
    if total > dynamic['fixup']:
        raise ValueError('fixup segments must remain inside original pass')
    return dict(zip(FIXUP_PHASES, row['nanoseconds']), totalObservedNs=total,
                unclassifiedFixupNs=dynamic['fixup'] - total, modules=row['calls'][0])


def parse_initial_stats(row):
    if (set(row) != {'startedNs', 'finishedNs', 'nanoseconds', 'calls'}
            or type(row['startedNs']) is not int or row['startedNs'] <= 0
            or type(row['finishedNs']) is not int or row['finishedNs'] < row['startedNs']
            or not isinstance(row['nanoseconds'], list) or not isinstance(row['calls'], list)
            or len(row['nanoseconds']) != len(INITIAL_PHASES)
            or len(row['calls']) != len(INITIAL_PHASES)
            or any(type(value) is not int or value < 0 for value in row['nanoseconds'])
            or any(type(value) is not int or value != 1 for value in row['calls'])):
        raise ValueError('all five original initial-setup phases must execute exactly once')
    total = sum(row['nanoseconds'])
    if total > row['finishedNs'] - row['startedNs']:
        raise ValueError('disjoint initial phases exceed their containing runtime interval')
    return dict(zip(INITIAL_PHASES, row['nanoseconds']), totalObservedNs=total,
                startedNs=row['startedNs'], finishedNs=row['finishedNs'],
                runtimeSinceInitialSetupNs=row['finishedNs'] - row['startedNs'])


def align_initial_interval(initial, process):
    if not process['launchedNs'] <= initial['startedNs'] <= initial['finishedNs'] <= process['finishedNs']:
        raise ValueError('child CLOCK_MONOTONIC must lie inside parent launch/finish interval')
    return dict(initial, launchToInitialSetupNs=initial['startedNs'] - process['launchedNs'],
                reportToParentFinishNs=process['finishedNs'] - initial['finishedNs'])


def parse_stats(row):
    keys = ('digestNs', 'providerNs', 'dlopenNs', 'digestCalls', 'providerCalls', 'dlopenCalls',
            'setupNs', 'linkerNs', 'setupCalls', 'linkerCalls')
    if set(row) != set(keys) or any(type(row[key]) is not int or row[key] < 0 for key in keys):
        raise ValueError('complete nonnegative loader counters required')
    if not row['providerCalls'] or row['digestCalls'] > row['providerCalls']:
        raise ValueError('real provider calls required')
    if row['providerNs'] < row['digestNs']:
        raise ValueError('digest interval must remain inside provider interval')
    return dict(row, providerOwnNs=row['providerNs'] - row['digestNs'])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--export-host', type=Path)
    parser.add_argument('--initial-setup', action='store_true')
    parser.add_argument('--initial-setup-only', action='store_true')
    parser.add_argument('--dynamic-setup', action='store_true')
    parser.add_argument('--fixup-detail', action='store_true')
    parser.add_argument('--loader-cpu', action='store_true')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    output = args.output.resolve()
    if os.uname().sysname != 'Darwin' or not output.is_relative_to(root / '.data') or output.exists():
        parser.error('fresh persistent isolated Darwin output required')
    if args.initial_setup_only and not args.initial_setup:
        parser.error('initial-setup-only requires initial-setup instrumentation')
    if args.dynamic_setup and (args.initial_setup_only or args.export_host):
        parser.error('dynamic setup requires real module import diagnostics')
    if args.fixup_detail and not args.dynamic_setup:
        parser.error('fixup detail requires containing dynamic setup measurement')
    if args.loader_cpu and (args.initial_setup or args.dynamic_setup or args.export_host):
        parser.error('CPU diagnostic requires ordinary loader boundaries without extra observers')
    retained = root / '.data/d1510-reader-whitespace-native-v2'
    if args.export_host:
        if args.initial_setup:
            parser.error('export does not reconstruct initial-setup diagnostics')
        previous = args.export_host.resolve()
        if not previous.is_relative_to(root / '.data'):
            parser.error('persistent diagnostic input required')
        receipt = json.loads((previous / 'report.json').read_text())
        if not receipt['qualified'] or not receipt['baselineUnchanged'] or digest(retained / 'gerbil') != FROZEN:
            raise ValueError('completed diagnostic and unchanged baseline required')
        if digest(previous / 'gerbil') != receipt['diagnosticBinarySha256']:
            raise ValueError('diagnostic binary changed')
        output.mkdir()
        shutil.copy2(previous / 'gerbil', output / 'gerbil')
        (output / 'gxi').symlink_to('gerbil')
        manifest = dict(qualified=True, performanceQualified=False, productionAdmitted=False,
                        scope='completed-loader-diagnostic-controller-identity-only',
                        binarySha256=receipt['diagnosticBinarySha256'], retainedBinarySha256=FROZEN,
                        diagnosticReportSha256=digest(previous / 'report.json'))
        (output / 'report.json').write_text(json.dumps(manifest, indent=2) + '\n')
        print(json.dumps(manifest))
        return 0
    manifest = json.loads((retained / 'report.json').read_text())
    if not manifest['qualified'] or digest(retained / 'gerbil') != FROZEN:
        raise ValueError('retained host identity changed')
    identities = {**manifest['frozenObjectHashes'], **manifest['privateRuntimeObjects']}
    if any(digest(root / path) != expected for path, expected in identities.items()):
        raise ValueError('retained object identity changed')
    report = dict(qualified=False, performanceQualified=False, productionAdmitted=False,
                  scope='retained-native-loader-diagnostic-only', binarySha256=FROZEN,
                  initialSetupRequested=args.initial_setup, steps=[], runs=[])
    report['dynamicSetupRequested'] = args.dynamic_setup
    report['fixupDetailRequested'] = args.fixup_detail
    report['loaderCpuRequested'] = args.loader_cpu
    if args.initial_setup_only:
        report['scope'] = 'retained-native-initial-setup-diagnostic-only'
    env = build_environment()
    env['GERBIL_BUILD_CORES'] = subprocess.check_output(['sysctl', '-n', 'hw.physicalcpu'], text=True).strip()
    output.mkdir()
    home = root / '.data/d1391-runtime-object-source/build'
    test_home = root / '.data/d1510-mcp-test-source-home-v2/build'
    lib = root / '.data/d1391-runtime-object-source/src/gambit/lib'
    driver = root / '.data/d1510-shell-substitution/bin'
    source = output / 'os_dyn_probe.c'
    source.write_text(instrument((retained / 'os_dyn_embedded.c').read_text()))

    def run(name, command, local, timeout):
        start = time.monotonic()
        with (output / (name + '.log')).open('w') as log:
            launched = time.clock_gettime_ns(time.CLOCK_MONOTONIC)
            child = subprocess.Popen(command, env=local, cwd=output, stdout=log,
                                     stderr=subprocess.STDOUT, start_new_session=True)
            try:
                child.wait(timeout=timeout)
            finally:
                if child.poll() is None:
                    force_stop(child)
            finished = time.clock_gettime_ns(time.CLOCK_MONOTONIC)
        row = dict(name=name, wallSeconds=time.monotonic() - start, exitCode=child.returncode,
                   launchedNs=launched, finishedNs=finished)
        report['steps'].append(row)
        if child.returncode:
            raise ValueError('diagnostic process failed: ' + name)
        return row

    try:
        local = dict(env, GERBIL_HOME=str(home), GAMBITDIR_INCLUDE=str(home / 'include'),
                     GAMBITDIR_LIB=str(home / 'lib'), BUILD_OBJ_INPUT_FILENAMES_PARAM=str(source),
                     BUILD_OBJ_OUTPUT_FILENAME_PARAM=str(source.with_suffix('.o')),
                     BUILD_OBJ_META_INFO_FILE_PARAM=str(source),
                     BUILD_OBJ_CC_OPTIONS_PARAM=f'-O3 -D___LIBRARY -DHAVE_CONFIG_H -I{lib} -I{lib.parent / "include"}')
        run('compile', [str(driver / 'gambuild-C'), 'obj'], local, 50)
        setup_source = output / 'setup_probe.c'
        original_setup = lib / 'setup.c'
        report['setupSourceSha256'] = digest(original_setup)
        setup_code = instrument_setup(original_setup.read_text(), args.initial_setup)
        if args.dynamic_setup:
            setup_code = instrument_dynamic_walks(setup_code)
        if args.fixup_detail:
            setup_code = instrument_fixup_detail(setup_code)
        if args.loader_cpu:
            loader_code, setup_code = instrument_loader_cpu(source.read_text(), setup_code)
            source.write_text(loader_code)
            # Recompile the private backend after adding CPU observation helpers.
            run('compile-cpu-backend', [str(driver / 'gambuild-C'), 'obj'], local, 50)
        setup_source.write_text(setup_code)
        setup_env = dict(local, BUILD_OBJ_INPUT_FILENAMES_PARAM=str(setup_source),
                         BUILD_OBJ_OUTPUT_FILENAME_PARAM=str(setup_source.with_suffix('.o')),
                         BUILD_OBJ_META_INFO_FILE_PARAM=str(setup_source))
        run('compile-setup', [str(driver / 'gambuild-C'), 'obj'], setup_env, 50)
        objects = [root / path for path in manifest['frozenObjectHashes'] if not path.endswith('libgambit.a')]
        providers = [retained / f'{index}.o' for index in range(len(manifest['providers']))]
        if any(digest(path) != row['renamedObjectSha256'] for path, row in zip(providers, manifest['providers'])):
            raise ValueError('provider bytes changed')
        run('link', [env['CC'], '-o', str(output / 'gerbil'), *map(str, objects),
                    *map(str, providers), str(source.with_suffix('.o')), str(setup_source.with_suffix('.o')),
                    *map(str, (root / path for path in manifest['privateRuntimeObjects'])),
                    str(home / 'lib/libgambit.a'), '-ldl', '-lm'], env, 50)
        report['diagnosticBinarySha256'] = digest(output / 'gerbil')
        (output / 'gxi').symlink_to('gerbil')
        # The control must have the gxi basename for the original dispatch.
        (output / 'control').mkdir()
        (output / 'control/gxi').symlink_to(retained / 'gerbil')
        (output / 'package-home').mkdir()
        for key in tuple(env):
            if key.startswith(('GAMBIT_DARWIN_', 'GERBIL_MCP_')):
                env.pop(key)
        env.pop('GERBIL_BUILD_PREFIX', None)
        env.update(GERBIL_HOME=str(test_home), GERBIL_PATH=str(output / 'package-home'),
                   GERBIL_LOADPATH=str(test_home / 'lib'), GAMBIT_EMBEDDED_NATIVE='0')
        fixture = Path(__file__).with_name('stdlib_import_cost.scm')
        if args.initial_setup:
            boot_prefix = output / 'boot-initial'
            local = dict(env, GB_INITIAL_SETUP_STATS=str(boot_prefix))
            process = run('boot', [str(output / 'gxi'), '-e', '(display "BOOT-OK\\n")'], local, 20)
            boot_files = list(output.glob('boot-initial.*.json'))
            if (len(boot_files) != 1 or (output / 'boot.log').read_text().splitlines() != ['BOOT-OK']):
                raise ValueError('real boot completion and exactly one initial-setup receipt required')
            report['boot'] = dict(processSeconds=process['wallSeconds'],
                initialSetup=align_initial_interval(parse_initial_stats(json.loads(boot_files[0].read_text())), process))
        if args.initial_setup_only:
            report['baselineUnchanged'] = digest(retained / 'gerbil') == FROZEN and digest(original_setup) == report['setupSourceSha256'] and all(
                digest(root / path) == expected for path, expected in identities.items())
            report['qualified'] = report['baselineUnchanged'] and bool(report.get('boot'))
            (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
            print(json.dumps({key: value for key, value in report.items() if key not in ('steps', 'runs')}))
            return 0 if report['qualified'] else 1
        for round_number in range(3):
            for module in (':std/make', ':std/test', ':std/encoding/json', ':std/list/list'):
                pair = []
                roles = ('control', 'probe') if round_number % 2 == 0 else ('probe', 'control')
                for role in roles:
                    name = f'{len(report["runs"])}-{role}'
                    stats_path = output / (name + '.json')
                    local = dict(env, GB_LOADER_STATS=str(stats_path))
                    if args.loader_cpu and role == 'probe':
                        local['GB_LOADER_CPU_STATS'] = str(output / (name + '-cpu'))
                    if args.dynamic_setup and role == 'probe':
                        local['GB_DYNAMIC_SETUP_STATS'] = str(output / (name + '-dynamic'))
                    if args.fixup_detail and role == 'probe':
                        local['GB_FIXUP_STATS'] = str(output / (name + '-fixup'))
                    if args.initial_setup and role == 'probe':
                        local['GB_INITIAL_SETUP_STATS'] = str(output / (name + '-initial'))
                    binary = output / ('control/gxi' if role == 'control' else 'gxi')
                    budget = (' (set! stdlib-process-budget? #t)'
                              ' (setenv "GB_LOADER_OBSERVE" "1")') if args.loader_cpu else ''
                    expression = '(begin (load ' + json.dumps(str(fixture)) + ')' + budget + " (stdlib-import-cost '" + module + '))'
                    process = run(name, [str(binary), '-e', expression], local, 20)
                    text = (output / (name + '.log')).read_text()
                    row = dict(role=role, module=module, round=round_number,
                               processSeconds=process['wallSeconds'], phases=parse_phases(text),
                               inventory=parse_inventory(text))
                    if args.loader_cpu:
                        row['budgets'] = parse_budgets(text)
                    if role == 'probe':
                        stats_files = list(output.glob(name + '.json.*.json'))
                        if len(stats_files) != 1:
                            raise ValueError('exactly one process loader receipt required')
                        row['loader'] = parse_stats(json.loads(stats_files[0].read_text()))
                        if args.loader_cpu:
                            cpu_files = list(output.glob(name + '-cpu.*.json'))
                            if len(cpu_files) != 1:
                                raise ValueError('exactly one completed loader CPU receipt required')
                            row['loaderCpu'] = parse_cpu_stats(json.loads(cpu_files[0].read_text()), row['loader'])
                        if args.dynamic_setup:
                            dynamic_files = list(output.glob(name + '-dynamic.*.json'))
                            if len(dynamic_files) != 1:
                                raise ValueError('exactly one completed dynamic setup receipt required')
                            row['dynamicSetup'] = parse_dynamic_stats(
                                json.loads(dynamic_files[0].read_text()), row['loader'])
                            if args.fixup_detail:
                                fixup_files = list(output.glob(name + '-fixup.*.json'))
                                if len(fixup_files) != 1:
                                    raise ValueError('exactly one completed fixup detail receipt required')
                                row['fixupDetail'] = parse_fixup_stats(
                                    json.loads(fixup_files[0].read_text()), row['dynamicSetup'])
                        if args.initial_setup:
                            initial_files = list(output.glob(name + '-initial.*.json'))
                            if len(initial_files) != 1:
                                raise ValueError('exactly one process initial-setup receipt required')
                            row['initialSetup'] = align_initial_interval(
                                parse_initial_stats(json.loads(initial_files[0].read_text())), process)
                    report['runs'].append(row)
                    pair.append(row)
                    print(json.dumps({k: v for k, v in row.items() if k not in ('inventory', 'budgets')}), flush=True)
                if pair[0]['inventory'] != pair[1]['inventory']:
                    raise ValueError('original export/module inventories differ')
        report['baselineUnchanged'] = digest(retained / 'gerbil') == FROZEN and digest(original_setup) == report['setupSourceSha256'] and all(
            digest(root / path) == expected for path, expected in identities.items())
        report['qualified'] = report['baselineUnchanged'] and len(report['runs']) == 24
    except Exception as error:
        report['failure'] = repr(error)
    finally:
        (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({key: value for key, value in report.items() if key not in ('steps', 'runs')}))
    return 0 if report['qualified'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
