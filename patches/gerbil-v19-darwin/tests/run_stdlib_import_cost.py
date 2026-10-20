"""Fresh-process standard-library import boundaries, not performance admission."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess
import time

from bazel_host_environment import build_environment
from progressive_performance_gate import force_stop


def parse_calls(text):
    rows, pending = [], []
    for line in text.splitlines():
        if not line.startswith('STDLIB-CALL\t'):
            continue
        fields = line.split('\t', 6)
        if len(fields) != 7:
            raise ValueError('complete traced call required')
        depth, kind, phase, state, seconds, key = fields[1:]
        depth, seconds = int(depth), float(seconds)
        if depth < 0 or not math.isfinite(seconds) or seconds < 0:
            raise ValueError('invalid call interval')
        if kind not in ('import', 'eval', 'scheme-compile', 'scheme-eval',
                        'gambit-prepare', 'gambit-run', 'gambit-demand', 'gambit-execute',
                        'native-module-load', 'interface-expand', 'interface-read', 'filesystem') or phase not in (
                'import', 'eval', 'cached-import', 'cached-eval'):
            raise ValueError('invalid trace boundary')
        if state not in ('exact-key-hit', 'no-exact-key', 'not-classified'):
            raise ValueError('invalid cache classification')
        children = []
        while pending and pending[-1]['depth'] > depth:
            child = pending.pop()
            if child['depth'] != depth + 1:
                raise ValueError('incomplete postorder trace')
            children.append(child)
        own = seconds - sum(child['seconds'] for child in children)
        if own < 0:
            raise ValueError('child intervals exceed parent')
        row = dict(depth=depth, kind=kind, phase=phase, state=state,
                   seconds=seconds, observedOwnSeconds=own, key=key)
        rows.append(row)
        pending.append(row)
    if not rows or any(row['depth'] != 0 for row in pending):
        raise ValueError('completed trace roots required')
    return rows


def parse_phases(text):
    rows = []
    for line in text.splitlines():
        if line.startswith('STDLIB-PHASE\t'):
            fields = line.split('\t')
            if len(fields) != 3:
                raise ValueError('phase and elapsed time required')
            seconds = float(fields[2])
            if not math.isfinite(seconds) or seconds < 0:
                raise ValueError('nonnegative finite elapsed time required')
            rows.append(dict(phase=fields[1], seconds=seconds))
    if [row['phase'] for row in rows] != ['import', 'eval', 'cached-import', 'cached-eval']:
        raise ValueError('all four ordered phase completions required')
    if text.splitlines()[-2:] != ['CONTEXT-IDENTITY-OK', 'OK']:
        raise ValueError('context identity and final OK required')
    return rows


def parse_inventory(text):
    exports = sorted(line.split('\t')[1:] for line in text.splitlines()
                     if line.startswith('STDLIB-EXPORT\t'))
    modules = sorted(line.split('\t')[1:] for line in text.splitlines()
                     if line.startswith('STDLIB-MODULE\t'))
    if not exports or not modules or any(len(row) != 2 for row in exports + modules):
        raise ValueError('nonempty export/native-module inventories required')
    if any(row[1] not in ('builtin', 'loaded') for row in modules):
        raise ValueError('all native modules must finish loading')
    return dict(exports=exports, modules=modules)


def parse_budgets(text):
    names = ('userSeconds', 'systemSeconds', 'realSeconds', 'gcUserSeconds',
             'gcSystemSeconds', 'gcRealSeconds', 'collections', 'allocatedBytesDelta',
             'minorFaults', 'majorFaults', 'latestGcHeapBytes', 'latestGcAllocatedBytes',
             'latestGcLiveBytes', 'latestGcMovableBytes', 'latestGcStillBytes')
    rows = []
    for line in text.splitlines():
        if not line.startswith('STDLIB-BUDGET\t'):
            continue
        fields = line.split('\t')
        if len(fields) != len(names) + 2:
            raise ValueError('complete process statistics required')
        values = list(map(float, fields[2:]))
        if any(not math.isfinite(value) or value < 0 for value in values):
            raise ValueError('finite nonnegative process statistics required')
        row = dict(zip(names, values), phase=fields[1])
        if any(not row[key].is_integer() for key in ('collections', 'minorFaults', 'majorFaults')):
            raise ValueError('integer process counters required')
        cpu = row['userSeconds'] + row['systemSeconds']
        gc_cpu = row['gcUserSeconds'] + row['gcSystemSeconds']
        if gc_cpu > cpu + 0.001:
            raise ValueError('GC CPU exceeds process CPU')
        row.update(cpuSeconds=cpu, gcCpuSeconds=gc_cpu,
                   gcCpuFraction=gc_cpu / cpu if cpu else None,
                   latestGcInThisPhase=row['collections'] > 0)
        rows.append(row)
    if [row['phase'] for row in rows] != ['import', 'eval', 'cached-import', 'cached-eval']:
        raise ValueError('four ordered process budgets required')
    return rows


def parse_binding_census(text):
    rows = []
    for line in text.splitlines():
        if not line.startswith('STDLIB-IMPORT-BINDINGS\t'):
            continue
        fields = line.split('\t')
        if len(fields) != 6:
            raise ValueError('complete import binding census required')
        context = fields[1]
        attempts, retained, strong, repeated = map(int, fields[2:])
        if not context or not 0 <= strong <= retained <= attempts or not 0 <= repeated <= attempts:
            raise ValueError('invalid import binding counts')
        rows.append(dict(context=context, attempts=attempts,
                         retainedPriorBinding=retained, strongRetainedPriorBinding=strong,
                         intraFormRepeatedKeys=repeated))
    if not rows or not sum(row['attempts'] for row in rows):
        raise ValueError('reached original import binding attempts required')
    return rows


def parse_reader_budgets(text, calls):
    rows = []
    for line in text.splitlines():
        if not line.startswith('STDLIB-READ-BUDGET\t'):
            continue
        fields = line.split('\t', 7)
        if len(fields) != 8:
            raise ValueError('complete reached reader budget required')
        depth, phase, user, system, gc, allocated, path = fields[1:]
        depth = int(depth)
        values = list(map(float, (user, system, gc, allocated)))
        if (depth < 0 or phase not in ('import', 'eval', 'cached-import', 'cached-eval')
                or any(not math.isfinite(value) for value in values)
                or any(value < 0 for value in values[:3])
                or values[2] > values[0] + values[1] + 0.001):
            raise ValueError('valid reader CPU/GC/allocation budget required')
        rows.append(dict(readDepth=depth, phase=phase, userSeconds=values[0],
                         systemSeconds=values[1], gcCpuSeconds=values[2],
                         allocatedBytesDelta=values[3], allocationDeltaNonnegative=values[3] >= 0,
                         path=path))
    reached = [call for call in calls if call['kind'] == 'interface-read']
    if (not rows or len(rows) != len(reached)
            or [(row['phase'], row['path']) for row in rows] !=
               [(call['phase'], call['key']) for call in reached]
            or text.splitlines().count('STDLIB-READER-RESTORED') != 1):
        raise ValueError('matched reached reader calls and restoration required')
    return rows


def parse_filesystem_budgets(text, calls):
    rows = []
    for line in text.splitlines():
        if not line.startswith('STDLIB-FILESYSTEM-BUDGET\t'):
            continue
        fields = line.split('\t')
        if len(fields) != 8:
            raise ValueError('complete filesystem budget required')
        op, phase, depth, user, system, minor, major = fields[1:]
        cpu = [float(user), float(system)]
        faults = [float(minor), float(major)]
        if (op not in ('file-info', 'normalize-directory')
                or phase not in ('import', 'eval', 'cached-import', 'cached-eval')
                or int(depth) != 0
                or any(not math.isfinite(value) or value < 0 for value in cpu + faults)
                or any(not value.is_integer() for value in faults)):
            raise ValueError('non-nested valid filesystem CPU/fault budget required')
        rows.append(dict(operation=op, phase=phase, userSeconds=cpu[0],
                         systemSeconds=cpu[1], minorFaults=int(faults[0]),
                         majorFaults=int(faults[1])))
    reached = [call for call in calls if call['kind'] == 'filesystem']
    if (not rows or {row['operation'] for row in rows} != {'file-info', 'normalize-directory'}
            or [(row['phase'], row['operation']) for row in rows] !=
               [(call['phase'], call['key']) for call in reached]
            or text.splitlines().count('STDLIB-FILESYSTEM-RESTORED') != 1):
        raise ValueError('matched filesystem calls and original restoration required')
    return rows


def parse_binding_budgets(text):
    rows = []
    for line in text.splitlines():
        if not line.startswith('STDLIB-BINDING-BUDGET\t'):
            continue
        fields = line.split('\t')
        if len(fields) != 9:
            raise ValueError('complete binding budget required')
        phase = fields[1]
        started, entered, returned = map(int, fields[2:5])
        entry_seconds, return_seconds, entry_bytes, return_bytes = map(float, fields[5:])
        values = (entry_seconds, return_seconds, entry_bytes, return_bytes)
        if (min(started, entered, returned) < 0 or started != entered or entered != returned
                or any(not math.isfinite(value) for value in values)
                or min(entry_seconds, return_seconds) < 0
                or not entry_bytes.is_integer() or not return_bytes.is_integer()
                or (started == 0 and any(values))):
            raise ValueError('completed nonnegative binding boundaries required')
        rows.append(dict(phase=phase, calls=started, entrySeconds=entry_seconds,
                         returnSeconds=return_seconds, entryAllocationMetricDeltaBytes=entry_bytes,
                         returnAllocationMetricDeltaBytes=return_bytes,
                         allocationDeltaNonnegative=min(entry_bytes, return_bytes) >= 0))
    if ([row['phase'] for row in rows] != ['import', 'eval', 'cached-import', 'cached-eval']
            or text.splitlines().count('STDLIB-BINDING-RESTORED') != 1):
        raise ValueError('all binding phases and original restoration required')
    return rows


def parse_length_budgets(text):
    rows = []
    for line in text.splitlines():
        if not line.startswith('STDLIB-LENGTH-BUDGET\t'):
            continue
        fields = line.split('\t')
        if len(fields) != 6:
            raise ValueError('complete syntax-length budget required')
        phase, calls, nodes, maximum, seconds = fields[1:]
        calls, nodes, maximum, seconds = int(calls), int(nodes), int(maximum), float(seconds)
        if (min(calls, nodes, maximum) < 0 or not math.isfinite(seconds) or seconds < 0
                or maximum > nodes or nodes > calls * maximum
                or (calls == 0 and (nodes != 0 or maximum != 0 or seconds != 0))):
            raise ValueError('consistent nonnegative syntax-length counters required')
        rows.append(dict(phase=phase, calls=calls, nodes=nodes, maximum=maximum, seconds=seconds))
    if ([row['phase'] for row in rows] != ['import', 'eval', 'cached-import', 'cached-eval']
            or text.splitlines().count('STDLIB-LENGTH-RESTORED') != 1):
        raise ValueError('all length phases and original restoration required')
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--attribution', action='store_true')
    parser.add_argument('--gambit-split', action='store_true')
    parser.add_argument('--interface-expand', action='store_true')
    parser.add_argument('--import-binding-census', action='store_true')
    parser.add_argument('--process-budget', action='store_true')
    parser.add_argument('--interface-read', action='store_true')
    parser.add_argument('--filesystem-budget', action='store_true')
    parser.add_argument('--hash-layout', action='store_true')
    parser.add_argument('--length-budget', action='store_true')
    parser.add_argument('--binding-budget', action='store_true')
    parser.add_argument('--module', choices=(':std/make', ':std/test', ':std/encoding/json', ':std/list/list'))
    parser.add_argument('--source-module', action='store_true')
    parser.add_argument('--native-allocation-report', type=Path)
    parser.add_argument('--native-allocation-source', type=Path)
    args = parser.parse_args()
    if args.native_allocation_source and not args.native_allocation_report:
        parser.error('native allocation source requires completed native diagnostic report')
    if args.native_allocation_report and (args.binding_budget or args.length_budget or
            args.gambit_split or args.interface_expand or args.interface_read or
            args.filesystem_budget or args.hash_layout or args.import_binding_census):
        parser.error('native allocation census excludes callback replacement observers')
    if args.binding_budget and (not args.attribution or args.length_budget or args.gambit_split
                               or args.interface_expand or args.interface_read
                               or args.filesystem_budget or args.hash_layout or args.import_binding_census):
        parser.error('binding observer requires attribution without other replacements')
    if args.source_module and (not args.attribution or not args.module):
        parser.error('source expansion requires a selected module and attribution')
    if args.length_budget and (not args.attribution or args.gambit_split or args.interface_expand
                              or args.interface_read or args.filesystem_budget or args.hash_layout):
        parser.error('length observer requires attribution without other replacements')
    if args.module and args.hash_layout:
        parser.error('physical hash snapshot retains its fixed make root')
    if args.hash_layout and (args.attribution or args.process_budget):
        parser.error('physical hash snapshot requires an uninstrumented import')
    if args.filesystem_budget and (not args.attribution or args.gambit_split or args.interface_expand
                                   or args.interface_read):
        parser.error('filesystem observer requires attribution without other replacements')
    if args.interface_read and (not args.attribution or args.gambit_split or args.interface_expand):
        parser.error('reader observer requires attribution without other replacements')
    if args.process_budget and args.attribution:
        parser.error('process budget requires original execution without callback observers')
    if args.gambit_split and not args.attribution:
        parser.error('Gambit split diagnostic requires attribution')
    if args.interface_expand and (not args.attribution or args.gambit_split):
        parser.error('interface observer requires attribution without evaluator replacement')
    if args.import_binding_census and not args.interface_expand:
        parser.error('binding census requires the reached interface observer')
    root = Path(__file__).resolve().parents[3]
    output = args.output.resolve()
    if not output.is_relative_to(root / '.data') or output.exists():
        parser.error('fresh persistent .data directory required')
    binary = root / '.data/d1510-reader-whitespace-native-v2/gerbil'
    home = root / '.data/d1510-mcp-test-source-home-v2/build'
    expected = '1f83878a01744817ceb6e74e5d07138948930a41386e568d156210ce9108bb21'
    if hashlib.sha256(binary.read_bytes()).hexdigest() != expected:
        raise ValueError('frozen host identity changed')
    physical_source = None
    if args.native_allocation_report:
        from gambit_allocation_sites import parse_counts
        native_report = args.native_allocation_report.resolve()
        if not native_report.is_relative_to(root / '.data'):
            raise ValueError('isolated native diagnostic report required')
        native = json.loads(native_report.read_text())
        if not (native.get('qualified') and native.get('inputsUnchanged') and
                native.get('controlMatchesRetained') and native.get('diagnosticOnly') is True):
            raise ValueError('byte-identical retained control and completed diagnostic required')
        binary = native_report.parent / 'gerbil'
        expected = native['binarySha256']
        if hashlib.sha256(binary.read_bytes()).hexdigest() != expected:
            raise ValueError('native diagnostic binary changed')
        physical_path = (args.native_allocation_source.resolve() if args.native_allocation_source else
                         root / '.data/d1391-runtime-object-source/src/gambit/lib/_thread.c')
        if not physical_path.is_relative_to(root / '.data'):
            raise ValueError('isolated original generated source required')
        if native['inputHashes'].get(str(physical_path.relative_to(root))) != hashlib.sha256(physical_path.read_bytes()).hexdigest():
            raise ValueError('original generated source identity required')
        physical_source = physical_path.read_text()
    output.mkdir()
    (output / 'gxi').symlink_to(binary)
    (output / 'package-home').mkdir()
    env = build_environment()
    for key in tuple(env):
        if key.startswith('GAMBIT_DARWIN_') or key.startswith('GERBIL_MCP_'):
            env.pop(key)
    env.pop('GERBIL_BUILD_PREFIX', None)
    env.update(GERBIL_HOME=str(home), GERBIL_PATH=str(output / 'package-home'),
               GERBIL_LOADPATH=str(home / 'lib'), GAMBIT_EMBEDDED_NATIVE='0')
    fixture = Path(__file__).with_name('stdlib_import_cost.scm')
    trace = fixture.with_name('stdlib_import_trace.scm')
    report = dict(scope='independent-standard-library-fresh-process-boundaries',
                  qualified=False, performanceQualified=False, productionAdmitted=False,
                  binarySha256=expected, consumerPackages=[],
                  fixtureSha256=hashlib.sha256(fixture.read_bytes()).hexdigest(),
                  traceSha256=hashlib.sha256(trace.read_bytes()).hexdigest() if args.attribution else None,
                  attributionRequested=args.attribution, runs=[])
    report['gambitSplitDiagnostic'] = args.gambit_split
    report['interfaceTransformerDiagnostic'] = args.interface_expand
    report['importBindingCensus'] = args.import_binding_census
    report['processBudget'] = args.process_budget
    report['interfaceReadDiagnostic'] = args.interface_read
    report['filesystemBudgetDiagnostic'] = args.filesystem_budget
    report['hashLayoutDiagnostic'] = args.hash_layout
    report['lengthBudgetDiagnostic'] = args.length_budget
    report['bindingBudgetDiagnostic'] = args.binding_budget
    report['nativePhysicalAllocationDiagnostic'] = physical_source is not None
    if physical_source is not None:
        report['physicalSourceSha256'] = hashlib.sha256(physical_path.read_bytes()).hexdigest()
        report['physicalCoverage'] = 'selected-generated-source-ALLOC-only; excludes-other-units-and-runtime-allocators'
        report['physicalSource'] = str(physical_path.relative_to(root))
    source = None
    if args.source_module:
        source = root / '.data/d935-staging-source/src/std' / (args.module[5:] + '.ss')
        report['sourceExpansionDiagnostic'] = True
        report['sourceModule'] = str(source.relative_to(root))
        report['sourceSha256'] = hashlib.sha256(source.read_bytes()).hexdigest()
    try:
        rounds = 1 if args.attribution or args.hash_layout else 3
        modules = ((':std/make',) if args.hash_layout else
                   (':std/make', ':std/test', ':std/encoding/json', ':std/list/list'))
        if args.module:
            modules = (args.module,)
        for round_number in range(rounds):
            for module in modules:
                index = len(report['runs'])
                log_path = output / f'{index}.log'
                trace_load = (' (load ' + json.dumps(str(trace)) + ')') if args.attribution else ''
                if args.process_budget:
                    trace_load += ' (set! stdlib-process-budget? #t)'
                if args.gambit_split:
                    trace_load += ' (install-stdlib-gambit-split!)'
                emit = ' emit-stdlib-trace!' if args.attribution else ''
                if args.length_budget:
                    trace_load += ' (install-stdlib-length!)'
                    emit = ' emit-stdlib-length-trace!'
                if args.binding_budget:
                    trace_load += ' (install-stdlib-binding!)'
                    emit = ' emit-stdlib-binding-trace!'
                if args.hash_layout:
                    emit = ' stdlib-emit-hash-layout!'
                if args.interface_read:
                    trace_load += ' (install-stdlib-interface-reader!)'
                    emit = ' emit-stdlib-reader-trace!'
                if args.filesystem_budget:
                    trace_load += ' (install-stdlib-filesystem!)'
                    emit = ' emit-stdlib-filesystem-trace!'
                if args.interface_expand:
                    trace_load += ' (install-stdlib-interface-expand!)'
                    emit = ' emit-stdlib-interface-trace!'
                if args.import_binding_census:
                    trace_load += ' (set! stdlib-import-binding-census? #t)'
                target = json.dumps(str(source)) if source else "'" + module
                expression = '(begin (load ' + json.dumps(str(fixture)) + ')' + trace_load + \
                             ' (stdlib-import-cost ' + target + emit + '))'
                started = time.monotonic()
                if physical_source is not None:
                    env['GAMBIT_PHYSICAL_ALLOCATION_PREFIX'] = str(output / f'{index}-allocation')
                with log_path.open('wb') as log:
                    child = subprocess.Popen([str(output / 'gxi'), '-e', expression],
                        cwd=output, env=env, stdout=log, stderr=subprocess.STDOUT,
                        start_new_session=True)
                    try:
                        child.wait(timeout=20)
                    finally:
                        if child.poll() is None:
                            force_stop(child)
                text = log_path.read_text(errors='replace')
                row = dict(module=module, round=round_number, exitCode=child.returncode,
                           processSeconds=time.monotonic() - started, passed=False)
                report['runs'].append(row)
                if child.returncode != 0 or '*** ERROR' in text:
                    raise ValueError(f'original standard-library execution failed: {module}')
                row['phases'] = parse_phases(text)
                row['inventory'] = parse_inventory(text)
                if physical_source is not None:
                    counters = list(output.glob(f'{index}-allocation.*.tsv'))
                    if len(counters) != 1:
                        raise ValueError('one completed original-process allocation dump required')
                    row['physicalAllocationSites'] = parse_counts(counters[0].read_text(), physical_source)
                    row['physicalAllocationWords'] = sum(site['physicalWords'] for site in row['physicalAllocationSites'])
                if args.length_budget:
                    row['lengthBudgets'] = parse_length_budgets(text)
                    row['lengthObserverReached'] = any(budget['calls'] for budget in row['lengthBudgets'])
                if args.binding_budget:
                    row['bindingBudgets'] = parse_binding_budgets(text)
                    row['bindingObserverReached'] = any(budget['calls'] for budget in row['bindingBudgets'])
                    row['bindingAllocationMetricNonnegative'] = all(
                        budget['allocationDeltaNonnegative'] for budget in row['bindingBudgets'])
                    row['physicalAllocationBudgetQualified'] = False
                    row['bindingAllocationMetricScope'] = 'get-bytes-allocated-stack-heap-still-plus-observer'
                if args.hash_layout and text.splitlines().count('STDLIB-HASH-LAYOUT-OK') != 1:
                    raise ValueError('completed physical hash snapshot required')
                if args.process_budget:
                    row['budgets'] = parse_budgets(text)
                if args.attribution:
                    row['calls'] = parse_calls(text)
                    if args.filesystem_budget:
                        row['filesystemBudgets'] = parse_filesystem_budgets(text, row['calls'])
                    if args.interface_read:
                        row['readerBudgets'] = parse_reader_budgets(text, row['calls'])
                        row['readerAllocationBudgetQualified'] = all(
                            budget['allocationDeltaNonnegative'] for budget in row['readerBudgets'])
                    if args.interface_expand and (
                            text.splitlines().count('STDLIB-INTERFACE-RESTORED') != 1
                            or not any(call['kind'] == 'interface-expand'
                                       for call in row['calls'])):
                        raise ValueError('reached and restored interface entries required')
                    if args.import_binding_census:
                        row['bindingCensus'] = parse_binding_census(text)
                    if args.gambit_split and not any(
                            call['kind'] == 'native-module-load' for call in row['calls']):
                        raise ValueError('requested native load boundary recorded no calls')
                row['passed'] = True
                print(json.dumps({key: value for key, value in row.items()
                                  if key not in ('calls', 'inventory', 'bindingCensus', 'budgets', 'readerBudgets', 'filesystemBudgets', 'physicalAllocationSites')}), flush=True)
        report['binaryUnchanged'] = hashlib.sha256(binary.read_bytes()).hexdigest() == expected
        if source:
            report['sourceUnchanged'] = hashlib.sha256(source.read_bytes()).hexdigest() == report['sourceSha256']
            if not report['sourceUnchanged']:
                raise ValueError('original standard-library source changed')
        report['qualified'] = len(report['runs']) == rounds * len(modules) and report['binaryUnchanged']
    except Exception as error:
        report['failure'] = repr(error)
    (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({key: value for key, value in report.items() if key != 'runs'}))
    return 0 if report['qualified'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
