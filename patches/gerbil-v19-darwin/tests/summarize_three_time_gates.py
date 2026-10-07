"""Separate candidate identity, three timing gates, and semantic acceptance."""
import argparse
import hashlib
import json
import math
from pathlib import Path


def within(value, ceiling):
    return type(value) in (int, float) and math.isfinite(value) and 0 < value <= ceiling


def summarize(cold, tests=None):
    runs = cold.get('runs', [])
    identities = {row.get('binarySha256') for row in runs}
    if not runs or len(identities) != 1 or None in identities:
        raise ValueError('one explicit candidate identity required')
    identity = next(iter(identities))
    if tests is not None and tests.get('binarySha256') != identity:
        raise ValueError('cannot combine different candidates build and test results')
    rows = []
    for index, row in enumerate(runs):
        first = row.get('firstCompileSeconds')
        complete = row.get('buildWallSeconds')
        rows.append(dict(round=index, firstLogSeconds=first,
                         firstLogGate='ALLOW' if within(first, 5) else 'DENY',
                         completeBuildSeconds=complete,
                         buildTimeGate='ALLOW' if within(complete, 50) else 'DENY',
                         completed=row.get('buildExitCode') == 0 and complete is not None,
                         sourceUnchanged=row.get('sourceUnchanged', cold.get('sourceUnchanged')) is True))
    three = len(rows) == 3
    first_pass = all(row['firstLogGate'] == 'ALLOW' for row in rows)
    build_pass = three and all(row['buildTimeGate'] == 'ALLOW' and row['completed'] and
                              row['sourceUnchanged'] for row in rows)
    test = dict(durationSeconds=None, durationGate='SKIP', correctnessGate='SKIP')
    if tests is not None:
        files = tests.get('runs', [])
        elapsed = tests.get('waveWallSeconds')
        correctness = (len(files) == 39 and tests.get('expectedCases') == 965 and
                       all(row.get('passed') is True for row in files))
        test.update(durationSeconds=elapsed, durationGate='ALLOW' if within(elapsed, 52) else 'DENY',
                    correctnessGate='ALLOW' if correctness else 'DENY',
                    passedFiles=sum(row.get('passed') is True for row in files),
                    deniedFiles=sum(row.get('passed') is not True for row in files),
                    successfulCompleteTestSeconds=elapsed if correctness else None)
    admitted = three and first_pass and build_pass and test['durationGate'] == test['correctnessGate'] == 'ALLOW'
    return dict(candidateBinarySha256=identity, requiredColdRuns=3, attemptedColdRuns=len(rows),
                limitsSeconds=dict(firstLog=5, completeBuild=50, completeTest=52), coldRuns=rows,
                firstLogGate='ALLOW' if first_pass else 'DENY', coldRepeatGate='ALLOW' if three else 'INCOMPLETE',
                completeColdBuildGate='ALLOW' if build_pass else 'DENY', test=test,
                decision='ALLOW' if admitted else 'DENY')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--cold-report', type=Path, required=True)
    parser.add_argument('--test-report', type=Path)
    parser.add_argument('--label', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    paths = [args.cold_report.resolve(), args.output.resolve()]
    if args.test_report:
        paths.append(args.test_report.resolve())
    if any(not path.is_relative_to(root / '.data') for path in paths) or paths[1].exists():
        parser.error('isolated input and fresh persistent output required')
    cold = json.loads(paths[0].read_text())
    tests = json.loads(paths[2].read_text()) if args.test_report else None
    result = summarize(cold, tests)
    result['candidateLabel'] = args.label
    inputs = [paths[0]] + ([paths[2]] if args.test_report else [])
    result['inputHashes'] = {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
                             for path in inputs}
    paths[1].parent.mkdir(parents=True, exist_ok=True)
    paths[1].write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
