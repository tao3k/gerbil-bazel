"""Fail-closed admission for extensions of the retained D1510 cold-build line."""
import argparse
import hashlib
import json
import math
from pathlib import Path

CEILING_SECONDS = 55


def admission(report, driver_hash):
    failures = []
    if report.get('buildPerformanceCeilingSeconds') != CEILING_SECONDS:
        failures.append('changed-performance-ceiling')
    if report.get('candidateDriverSha256') != driver_hash:
        failures.append('driver-identity-mismatch')
    if report.get('qualified') is not True or report.get('sourceUnchanged') is not True:
        failures.append('product-or-source-check-failed')
    rows = [row for row in report.get('runs', []) if row.get('role') == 'candidate']
    if not rows:
        failures.append('no-candidate-build')
    for index, row in enumerate(rows):
        elapsed = row.get('buildWallSeconds')
        if (type(elapsed) not in (int, float) or not math.isfinite(elapsed)
                or elapsed <= 0 or elapsed > CEILING_SECONDS):
            failures.append(f'candidate-{index}-over-ceiling-or-invalid-duration')
        if not (row.get('passed') is True and row.get('sourceUnchanged') is True
                and row.get('nativeImagesAfterClean') == 0
                and row.get('cleanExitCode') == 0 and row.get('buildExitCode') == 0
                and row.get('cleanTerminalExitCode') == 0
                and row.get('buildTerminalExitCode') == 0):
            failures.append(f'candidate-{index}-cold-build-check-failed')
    return dict(decision='DENY' if failures else 'ALLOW', admitted=not failures,
                ceilingSeconds=CEILING_SECONDS, candidateCount=len(rows),
                driverSha256=driver_hash, failures=failures,
                scope='complete-cold-build-only-not-startup-or-test-speedup')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--driver', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = admission(json.loads(args.report.read_text()),
                       hashlib.sha256(args.driver.read_bytes()).hexdigest())
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))
    return 0 if result['admitted'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
