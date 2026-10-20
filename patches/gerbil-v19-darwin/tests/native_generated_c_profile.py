"""Content-bound native experiment identity; not performance admission."""
import hashlib
import json
import argparse
from pathlib import Path


def verify_native_profile(root, driver, *, in_process_digests=False, planned_producers=False,
                          closed_link_profile=None, runtime=None):
    stack = root / 'patches/gerbil-v19-darwin'
    if planned_producers and not in_process_digests:
        raise ValueError('planned producer profile requires compiled digests')
    if closed_link_profile:
        if planned_producers or not in_process_digests or runtime is None:
            raise ValueError('closed link requires compiled digests and matching runtime, without singleton producers')
        return verify_build_lock(root, driver, closed_link_profile, runtime)
    version = 'v11' if planned_producers else 'v9' if in_process_digests else 'v8'
    return verify_build_lock(root, driver, stack / f'receipts/d1510-native-generated-c-profile-{version}.json')


def verify_build_lock(root, driver, lock_path, runtime=None):
    stack = root / 'patches/gerbil-v19-darwin'
    lock = json.loads(lock_path.read_text())
    driver = driver.resolve()
    if not driver.is_relative_to(root / '.data'):
        raise ValueError('native GSC profile must be isolated')
    for group, base in ((lock['files'], driver), (lock['entrySources'], driver.parent)):
        for name, expected in group.items():
            if Path(name).is_absolute() or '..' in Path(name).parts:
                raise ValueError('invalid native identity path')
            path = base / name
            if not path.is_file() or path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
                raise ValueError('native GSC profile identity drift: ' + name)
    for name, expected in lock['sources'].items():
        for path in (stack / 'tests' / name, driver.parent / 'gsc' / name):
            if not path.is_file() or path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
                raise ValueError('native GSC compiled source drift: ' + name)
    for group, base in ((lock.get('inputs', {}), stack / 'tests'),
                        (lock.get('patches', {}), stack),
                        (lock.get('runtimeFiles', {}), runtime)):
        for name, expected in group.items():
            if base is None or Path(name).is_absolute() or '..' in Path(name).parts:
                raise ValueError('matching runtime and relative identity paths required')
            path = base / name
            if path.is_symlink() or not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
                raise ValueError('native build prerequisite drift: ' + name)
    return dict(lock['files'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--driver', type=Path, required=True)
    parser.add_argument('--lock', type=Path, required=True)
    parser.add_argument('--runtime', type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    try:
        verify_build_lock(root, args.driver, args.lock, args.runtime)
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(1, f'NATIVE-BUILD-IDENTITY-DENY {error}\n')
    print('NATIVE-BUILD-IDENTITY-OK identity-only-not-performance-admission')
