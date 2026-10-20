"""Verify a content-locked patch series before touching a replay fixture."""

import argparse
import hashlib
import json
import math
from pathlib import Path


def local_file(directory, name):
    if not name or Path(name).name != name or name in {'.', '..'}:
        raise ValueError(f'Invalid locked filename: {name!r}')
    path = directory / name
    if path.is_symlink() or not path.is_file():
        raise ValueError(f'Locked file must be a regular non-symlink: {name}')
    return path


def verify_digest(directory, name, expected):
    actual = hashlib.sha256(local_file(directory, name).read_bytes()).hexdigest()
    if actual != expected:
        raise ValueError(f'Locked digest mismatch: {name}')


def evidence_file(directory, name):
    parts = name.split('/')
    if not name or '\\' in name or any(part in {'', '.', '..'} for part in parts):
        raise ValueError(f'Invalid evidence path: {name!r}')
    path = directory
    if path.is_symlink() or not path.is_dir():
        raise ValueError('Evidence root must be a regular non-symlink directory')
    for part in parts[:-1]:
        path = path / part
        if path.is_symlink() or not path.is_dir():
            raise ValueError(f'Evidence parent must be a regular non-symlink directory: {name}')
    return local_file(path, parts[-1])


def performance_records(lock_path, lock):
    policy_name = lock.get('performancePolicy')
    if policy_name is None:
        policies = [name for name in lock.get('receiptFiles', {})
                    if json.loads(local_file(lock_path.parent, name).read_text()).get('schema')
                    == 'mcp-performance-lock-v1']
        if len(policies) != 1:
            raise ValueError('Expected one locked performance policy')
        policy_name = policies[0]
    if policy_name not in lock.get('receiptFiles', {}):
        raise ValueError('Missing locked performance policy')
    policy = json.loads(local_file(lock_path.parent, policy_name).read_text())
    measured = lock if 'coldSamples' in lock else policy
    return measured, policy


def verify_performance(lock_path, lock):
    measured, policy = performance_records(lock_path, lock)
    limits = policy['limitsSeconds']
    if measured.get('limitsSeconds') != limits:
        raise ValueError('Performance limits differ from frozen policy')

    def bounded(value, ceiling):
        return (type(value) in {int, float} and math.isfinite(value)
                and type(ceiling) in {int, float} and math.isfinite(ceiling)
                and 0 < value <= ceiling)

    samples = measured['coldSamples']
    if len(samples) < 3:
        raise ValueError('Three cold builds required')
    for index, sample in enumerate(samples):
        build = sample.get('completeBuildSeconds', sample.get('buildWallSeconds'))
        if not bounded(sample['firstCompileSeconds'], limits['firstLog']):
            raise ValueError(f'First-log performance DENY: sample {index + 1}')
        if not bounded(build, limits['completeBuild']):
            raise ValueError(f'Cold-build performance DENY: sample {index + 1}')
    test = measured['completeTest']
    if not bounded(test['wallSeconds'], limits['completeTest']):
        raise ValueError('Complete-test performance DENY')
    # Legacy receipts omit passed; an explicit status must be a true boolean.
    if ('passed' in test and test['passed'] is not True):
        raise ValueError('Complete-test status DENY')
    if (type(test['passingSamples']) is not int or test['passingSamples'] < 1
            or any(type(test[key]) is not int or test[key] < 1
                   or type(policy['completeTest'][key]) is not int
                   or test[key] != policy['completeTest'][key]
                   for key in ('files', 'cases'))):
        raise ValueError('Complete-test inventory DENY')


def performance_summary(lock_path):
    measured, policy = performance_records(lock_path, json.loads(lock_path.read_text()))
    limits = policy['limitsSeconds']
    lines = ['RETAINED-PERFORMANCE not-a-new-benchmark']
    for index, sample in enumerate(measured['coldSamples'], 1):
        build = sample.get('completeBuildSeconds', sample.get('buildWallSeconds'))
        lines.append(f'COLD {index} first={sample["firstCompileSeconds"]:.3f}s build={build:.3f}s')
    test = measured['completeTest']
    lines.append(f'FULL-TEST {test["wallSeconds"]:.3f}s files={test["files"]} '
                 f'cases={test["cases"]} passing-samples={test["passingSamples"]}')
    lines.append(f'GATES first={limits["firstLog"]:g}s build={limits["completeBuild"]:g}s '
                 f'test={limits["completeTest"]:g}s per-sample-no-averaging')
    return '\n'.join(lines)


def verify_patch_lock(lock_path, driver=None, runtime=None, evidence_root=None,
                      gsc=None, performance=False, lock_sha256=None):
    if lock_sha256 is not None:
        verify_digest(lock_path.parent, lock_path.name, lock_sha256)
    lock = json.loads(lock_path.read_text())
    stack = lock_path.parent.parent
    patches = lock['patches']
    series = local_file(stack, lock['series']).read_text().splitlines()
    if not series or series != list(patches) or len(set(series)) != len(series):
        raise ValueError('Locked patch order mismatch')
    for name in series:
        verify_digest(stack, name, patches[name])
    for name, digest in lock.get('receiptFiles', {}).items():
        verify_digest(lock_path.parent, name, digest)
    for name, digest in lock.get('sourceFiles', {}).items():
        verify_digest(stack / 'tests', name, digest)
    if driver is not None:
        files = lock['driverFiles']
        if not files:
            raise ValueError('Empty locked driver identity')
        for name, digest in files.items():
            verify_digest(driver, name, digest)
    if runtime is not None:
        files = lock.get('runtimeFiles')
        if not files:
            raise ValueError('Missing locked runtime identity')
        for name, digest in files.items():
            verify_digest(runtime, name, digest)
    if evidence_root is not None:
        files = lock.get('rawEvidenceFiles')
        if not files:
            raise ValueError('Missing locked raw evidence identity')
        for name, digest in files.items():
            actual = hashlib.sha256(evidence_file(evidence_root, name).read_bytes()).hexdigest()
            if actual != digest:
                raise ValueError(f'Locked raw evidence mismatch: {name}')
    if gsc is not None:
        expected = lock.get('gscSha256')
        if expected is None:
            raise ValueError('Missing locked GSC identity')
        verify_digest(gsc.parent, gsc.name, expected)
    if performance:
        verify_performance(lock_path, lock)
    return len(series)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('lock', type=Path)
    parser.add_argument('--driver', type=Path)
    parser.add_argument('--runtime', type=Path, help='directory containing locked runtime files')
    parser.add_argument('--evidence-root', type=Path, help='root containing locked raw measurement reports')
    parser.add_argument('--gsc', type=Path, help='selected regular GSC binary')
    parser.add_argument('--lock-sha256', help='expected identity of the entire qualification receipt')
    parser.add_argument('--performance', action='store_true', help='validate every frozen timing sample and complete test inventory')
    args = parser.parse_args()
    try:
        count = verify_patch_lock(args.lock, args.driver, args.runtime, args.evidence_root,
                                  args.gsc, args.performance, args.lock_sha256)
        summary = performance_summary(args.lock) if args.performance else None
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(1, f'PATCH-LOCK-DENY {error}\n')
    print(f'PATCH-LOCK-OK patches={count} driver={args.driver is not None} runtime={args.runtime is not None} evidence={args.evidence_root is not None} gsc={args.gsc is not None} performance={args.performance}')
    if summary is not None:
        print(summary)


if __name__ == '__main__':
    main()
