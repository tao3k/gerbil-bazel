"""Read terminal native receipts; never launch or supervise native tests."""
import argparse
import hashlib
import json
from pathlib import Path
import re


def read_native_receipt(root, directory, expected_cases):
    log_path = directory / 'output.log'
    text = log_path.read_text()
    status = int((directory / 'exit-status.txt').read_text())
    cases = len(re.findall(r'^CASE-OK ', text, re.MULTILINE))
    final_ok = bool(re.search(r'^OK$', text, re.MULTILINE))
    times = dict(re.findall(r'^(real|user|sys) ([0-9.]+)$',
                           (directory / 'time.txt').read_text(), re.MULTILINE))
    if set(times) != {'real', 'user', 'sys'}:
        raise ValueError('complete native process times required')
    return {
        'receipt': str(directory.relative_to(root)), 'exitStatus': status,
        'completeSeconds': float(times['real']), 'userSeconds': float(times['user']),
        'systemSeconds': float(times['sys']), 'cases': cases, 'finalOk': final_ok,
        'correctnessPassed': status == 0 and final_ok and cases == expected_cases,
        'staticObjectHits': len(re.findall(r'GAMBIT-STATIC-OBJECT-HIT', text)),
        'staticObjectMisses': len(re.findall(r'GAMBIT-STATIC-OBJECT-MISS', text)),
        'objectCalls': len(re.findall(r'/gsc -obj\b', text)),
        'generatedCHits': len(re.findall(r'GAMBIT-GENERATED-C-HIT', text)),
        'generatedCMisses': len(re.findall(r'GAMBIT-GENERATED-C-MISS', text)),
        'generatedCUncacheable': len(re.findall(r'GAMBIT-GENERATED-C-UNCACHEABLE', text)),
        'closedLinkSelections': [int(count) for count in re.findall(
            r'GAMBIT-CLOSED-LINK-SELECTED (\d+)', text)],
        'entryCacheHit': 'NATIVE-ENTRY-CACHE-HIT' in text,
        'entryCacheMiss': 'NATIVE-ENTRY-CACHE-MISS' in text,
        'outputSha256': hashlib.sha256(log_path.read_bytes()).hexdigest(),
    }


def read_native_suite_receipt(root, directory, expected_modules):
    """Admit a terminal full-pool receipt against an explicit module inventory."""
    if not expected_modules or len(set(expected_modules)) != len(expected_modules):
        raise ValueError('nonempty unique expected module inventory required')
    record = read_native_receipt(root, directory, -1)
    text = (directory / 'output.log').read_text()
    passed = re.findall(r'^\[ascent-test\] PASS (\S+)$', text, re.MULTILINE)
    plans = re.findall(r'^\[ascent-test\] PLAN parallel=(\d+) exclusive=(\d+) jobs=(\d+)$',
                       text, re.MULTILINE)
    plan_ok = (len(plans) == 1 and int(plans[0][2]) > 0
               and int(plans[0][0]) + int(plans[0][1]) == len(expected_modules))
    failures = bool(re.search(r'^\[ascent-test\] FAIL|^ERROR |^\*\*\* ERROR|Heap overflow|Stack overflow',
                              text, re.MULTILINE))
    inventory_ok = len(passed) == len(expected_modules) and set(passed) == set(expected_modules)
    record.update({'scope': 'complete-native-suite', 'expectedModules': len(expected_modules),
                   'passedModules': len(passed), 'moduleInventoryPassed': inventory_ok,
                   'planPassed': plan_ok,
                   'correctnessPassed': record['exitStatus'] == 0 and record['cases'] > 0
                   and plan_ok and inventory_ok and not failures
                   and len(re.findall(r'^OK$', text, re.MULTILINE)) == len(expected_modules)
                   # Nested native child controls can emit this marker too.
                   # Exact per-module PASS admission is owned by the native runner.
                   and len(re.findall(r'^NATIVE-MODULES-OK$', text, re.MULTILINE)) >= len(expected_modules)})
    return record


def admit_object_reuse(record, expected_events, minimum_hits):
    """Require real backend reuse, not an upper entry-cache hit or partial run."""
    if not 0 < minimum_hits <= expected_events:
        raise ValueError('positive bounded object HIT requirement needed')
    return (
        record['correctnessPassed'] and record['entryCacheMiss']
        and not record['entryCacheHit']
        and record['staticObjectHits'] >= minimum_hits
        and record['staticObjectHits'] + record['staticObjectMisses'] == expected_events
        and record['objectCalls'] >= expected_events
    )


def read_compile_failure_receipt(root, directory, expected_error):
    """Qualify a typed compile rejection, never count it as passing test Cases."""
    if not expected_error or not expected_error.strip():
        raise ValueError('specific expected compiler error required')
    record = read_native_receipt(root, directory, 0)
    text = (directory / 'output.log').read_text()
    started = len(re.findall(r'^CASE ', text, re.MULTILINE))
    record.update({
        'scope': 'expected-source-compilation-failure',
        'casesStarted': started,
        'failureRejected': (
            1 <= record['exitStatus'] < 124 and expected_error in text
            and started == 0 and record['cases'] == 0 and not record['finalOk']
            and not record['entryCacheHit']
            and not re.search(r'^HARNESS-OK|^SUITE-OK|^MODULE-OK', text, re.MULTILINE)
        ),
    })
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', action='append', type=Path, required=True)
    scope = parser.add_mutually_exclusive_group(required=True)
    scope.add_argument('--expected-cases', type=int)
    scope.add_argument('--modules-file', type=Path)
    scope.add_argument('--expected-compile-error', help='typed error for a rejected source fixture')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--reuse-events', type=int, help='exact backend event count, not a Suite inventory')
    parser.add_argument('--minimum-object-hits', type=int)
    args = parser.parse_args()
    reuse_requested = args.reuse_events is not None or args.minimum_object_hits is not None
    if reuse_requested and (args.reuse_events is None or args.minimum_object_hits is None
                            or args.expected_cases is None or args.expected_cases <= 0):
        parser.error('object reuse admission requires positive expected Cases, events and minimum HITs')
    root = Path(__file__).resolve().parents[4]
    if args.expected_compile_error is not None:
        runs = [read_compile_failure_receipt(root, path.resolve(), args.expected_compile_error)
                for path in args.run]
    elif args.modules_file:
        modules = args.modules_file.read_text().splitlines()
        runs = [read_native_suite_receipt(root, path.resolve(), modules) for path in args.run]
    else:
        runs = [read_native_receipt(root, path.resolve(), args.expected_cases) for path in args.run]
    if args.output.exists():
        raise ValueError('fresh summary required')
    summary = {'schema': 1, 'runs': runs,
        'correctnessPassed': all(run['correctnessPassed'] for run in runs)}
    if args.expected_compile_error is not None:
        summary['failureRejectionPassed'] = all(run['failureRejected'] for run in runs)
    if reuse_requested:
        for run in runs:
            run['objectReusePassed'] = admit_object_reuse(
                run, args.reuse_events, args.minimum_object_hits)
        summary['objectReusePassed'] = all(run['objectReusePassed'] for run in runs)
    args.output.write_text(json.dumps(summary, indent=2) + '\n')
    for run in runs:
        print(json.dumps(run))
    if reuse_requested and not summary['objectReusePassed']:
        raise SystemExit(2)


if __name__ == '__main__':
    main()
