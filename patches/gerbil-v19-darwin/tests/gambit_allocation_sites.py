"""Count physical generated allocation words; never infer wall-time savings."""
import re


def summarize_counts(rows, source):
    procedures, procedure, inside = {}, None, False
    for line, text in enumerate(source.splitlines(), 1):
        if text.startswith('#define ___PH_PROC '):
            procedure = text.split()[-1]
        if text.strip() == '___BEGIN_P_SW':
            inside = True
        procedures[line] = procedure if inside else None
        if text.strip() == '___END_P_SW':
            inside = False
    totals = {}
    for row in rows:
        name = procedures[row['line']]
        if name is None:
            raise ValueError('original lexical procedure required')
        total = totals.setdefault(name, dict(calls=0, physicalWords=0))
        total['calls'] += row['calls']
        total['physicalWords'] += row['physicalWords']
    return dict(physicalWords=sum(row['physicalWords'] for row in rows),
                allocationCalls=sum(row['calls'] for row in rows),
                byProcedure=totals)


def instrument(source):
    boundary = '#include "gambit.h"\n'
    if source.count(boundary) != 1 or 'gb_physical_calls' in source:
        raise ValueError('one original generated Gambit include required')
    if re.search(r'^\s*#\s*line\b', source, re.M):
        raise ValueError('source line remapping is unsupported')
    line = source[:source.index(boundary) + len(boundary)].count('\n') + 1
    size = source.count('\n') + 2
    header = f'''
#if !defined(__APPLE__) || !defined(__GNUC__) || defined(__clang__) || \\
    !defined(___SINGLE_VM) || !defined(___SINGLE_THREADED_VMS) || ___MAX_PROCESSORS != 1
#error "physical allocation diagnostic requires retained Darwin GNU single-processor VM"
#endif
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <limits.h>
static unsigned long long gb_physical_calls[{size}], gb_physical_words[{size}];
static unsigned long long gb_physical_errors;
#undef ___ALLOC
#define ___ALLOC(n) __extension__ ({{ ___WORD gb_n = (n); \\
  if (gb_physical_calls[__LINE__] == ULLONG_MAX || \\
      ULLONG_MAX - gb_physical_words[__LINE__] < gb_n) ++gb_physical_errors; \\
  else {{ ++gb_physical_calls[__LINE__]; gb_physical_words[__LINE__] += gb_n; }} \\
  ___hp += gb_n; }})
static void __attribute__((destructor)) gb_physical_dump(void) {{
  const char *prefix = getenv("GAMBIT_PHYSICAL_ALLOCATION_PREFIX");
  char path[4096];
  if (!prefix) return;
  int length = snprintf(path, sizeof(path), "%s.%ld.tsv", prefix, (long)getpid());
  if (length < 0 || length >= sizeof(path)) abort();
  FILE *file = fopen(path, "wx");
  if (!file) abort();
  if (fprintf(file, "ERRORS %llu\\n", gb_physical_errors) < 0) abort();
  for (unsigned site = 0; site < {size}; ++site)
    if (gb_physical_calls[site] && fprintf(file, "%u %llu %llu\\n", site,
          gb_physical_calls[site], gb_physical_words[site]) < 0) abort();
  if (fclose(file)) abort();
}}
#line {line}
'''
    result = source.replace(boundary, boundary + header, 1)
    if result.replace(boundary + header, boundary, 1) != source:
        raise ValueError('original generated source must remain intact')
    return result


def parse_counts(text, source):
    lines = text.splitlines()
    if not lines or lines[0] != 'ERRORS 0':
        raise ValueError('complete zero-error allocation counter required')
    original = source.splitlines()
    rows, seen = [], set()
    for line in lines[1:]:
        fields = line.split()
        if len(fields) != 3:
            raise ValueError('complete allocation site required')
        site, calls, words = map(int, fields)
        if (site in seen or not 1 <= site <= len(original) or calls <= 0 or words < calls
                or not re.search(r'___(?:END_ALLOC_|ALLOC_CLO\(|ALLOC\(|CONS\(|MAKECONTINUATION\(|F64BOX\()', original[site - 1])):
            raise ValueError(f'unique positive original allocation site required: {line}')
        seen.add(site)
        rows.append(dict(line=site, calls=calls, physicalWords=words))
    if not rows:
        raise ValueError('reached physical allocation sites required')
    return rows


def main():
    import argparse
    import json
    from pathlib import Path
    from native_object_manifest import digest
    from experiment_framework.context import data_path
    from run_stdlib_import_cost import parse_phases, parse_inventory

    parser = argparse.ArgumentParser(description='Reparse retained raw native allocation evidence, never retry workload.')
    for name in ('run', 'control', 'source', 'binary', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    paths = {name: data_path(root, getattr(args, name), fresh=name == 'output')
             for name in ('run', 'control', 'source', 'binary', 'output')}
    run, control = (json.loads(paths[name].read_text()) for name in ('run', 'control'))
    if (not run.get('nativePhysicalAllocationDiagnostic') or not control.get('qualified') or
            len(run['runs']) != 1 or len(control['runs']) != 1 or
            digest(paths['binary']) != run['binarySha256'] or
            digest(paths['source']) != run['physicalSourceSha256']):
        raise ValueError('unchanged original source, diagnostic binary and complete control required')
    current, original = run['runs'][0], control['runs'][0]
    log = paths['run'].parent / '0.log'
    text = log.read_text()
    if (current['exitCode'] != 0 or '*** ERROR' in text or current['module'] != original['module'] or
            parse_inventory(text) != original['inventory'] or
            parse_phases(text) != current['phases'] or
            run.get('sourceSha256') != control.get('sourceSha256')):
        raise ValueError('successful workload and exact matched inventory required')
    counters = list(paths['run'].parent.glob('0-allocation.*.tsv'))
    if len(counters) != 1:
        raise ValueError('one completed native counter dump required')
    source = paths['source'].read_text()
    rows = parse_counts(counters[0].read_text(), source)
    report = dict(scope='original-thread-physical-allocation-census-not-performance',
                  workloadPassed=True, inventoryMatchesControl=True,
                  performanceQualified=False, productionAdmitted=False,
                  coverage=run['physicalCoverage'], module=current['module'], sites=rows,
                  **summarize_counts(rows, source))
    report['inputHashes'] = {str(path.relative_to(root)): digest(path)
                            for name, path in paths.items() if name != 'output'}
    report['inputHashes'].update({str(path.relative_to(root)): digest(path) for path in (log, counters[0])})
    paths['output'].write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({key: value for key, value in report.items()
                      if key not in ('sites', 'byProcedure', 'inputHashes')}))


if __name__ == '__main__':
    main()
