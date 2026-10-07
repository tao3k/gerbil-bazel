"""Tightened source-loader gate without rewriting historical D1510 policy."""
import argparse
import hashlib
import json
from pathlib import Path

from admit_d1510_cold_build import admission

TARGET_SECONDS = 50
CEILING_SECONDS = 52


def repeat_admission(report, driver_hash):
    result = admission(report, driver_hash)
    failures = list(result['failures'])
    rows = [row for row in report.get('runs', []) if row.get('role') == 'candidate']
    for index, row in enumerate(rows):
        elapsed = row.get('buildWallSeconds')
        if type(elapsed) not in (int, float) or not 0 < elapsed <= CEILING_SECONDS:
            failures.append(f'candidate-{index}-over-52-second-ceiling-or-invalid-duration')
    return dict(result, decision='DENY' if failures else 'ALLOW',
                admitted=not failures, failures=failures,
                ceilingSeconds=CEILING_SECONDS, targetSeconds=TARGET_SECONDS,
                targetMet=bool(rows) and not failures and all(
                    row['buildWallSeconds'] <= TARGET_SECONDS for row in rows))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--driver', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = repeat_admission(json.loads(args.report.read_text()),
                              hashlib.sha256(args.driver.read_bytes()).hexdigest())
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))
    return 0 if result['admitted'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
