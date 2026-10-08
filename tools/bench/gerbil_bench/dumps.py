"""Reviewed cleanup for legacy compiler dumps and isolated package build caches."""
import json
import os
from pathlib import Path
import re
import subprocess
import shutil
import time

from .protection import intersects, protected_paths
from .storage import atomic_json, digest, fingerprint, lease, relative


DUMP_NAME = re.compile(r'.+\.\d{3,}[irt]\.[A-Za-z0-9_.-]+$')


def file_identity(path):
    stat = path.stat(follow_symlinks=False)
    return dict(bytes=stat.st_size, mtimeNs=stat.st_mtime_ns, inode=stat.st_ino, device=stat.st_dev)


def plan(root, directories, seconds=15, *, kind='dumps'):
    if kind not in ('dumps', 'package-caches'):
        raise ValueError('known legacy artifact class required')
    root = root.resolve()
    protected = protected_paths(root)
    targets, blocked = [], []
    started = time.monotonic()
    complete = True
    for name in directories:
        directory = relative(root, name)
        if (root / name != directory or not directory.is_relative_to(root / '.data') or
            not directory.is_dir()):
            raise ValueError('existing isolated .data directory required')
        for folder, dirs, names in os.walk(directory, followlinks=False):
            dirs[:] = sorted(name for name in dirs if not os.path.islink(os.path.join(folder, name)))
            current = Path(folder)
            if time.monotonic() - started >= seconds:
                complete = False
                break
            if kind == 'package-caches':
                if current.name == '.gerbil' and current.parent.name == 'project' and (current.parent / 'gerbil.pkg').is_file():
                    for leaf in ('lib', 'bin'):
                        path = current / leaf
                        if not path.is_dir() or path.is_symlink():
                            continue
                        if intersects(path.resolve(), protected):
                            blocked.append(str(path.relative_to(root)))
                            continue
                        try:
                            metadata = fingerprint(path, deadline=started + seconds)
                        except TimeoutError:
                            complete = False
                            break
                        except ValueError:
                            blocked.append(str(path.relative_to(root)))
                            continue
                        targets.append(dict(path=str(path.relative_to(root)), kind=kind,
                            projectPkgSha256=digest(current.parent / 'gerbil.pkg'), **metadata))
                    dirs[:] = []
                    if not complete:
                        break
                continue
            for filename in sorted(names):
                if time.monotonic() - started >= seconds:
                    complete = False
                    break
                if not DUMP_NAME.fullmatch(filename):
                    continue
                raw = Path(folder) / filename
                if raw.is_symlink() or not raw.is_file():
                    continue
                path = relative(root, str(raw.relative_to(root)))
                if intersects(path, protected):
                    blocked.append(str(path.relative_to(root)))
                else:
                    targets.append(dict(path=str(path.relative_to(root)), kind=kind, **file_identity(path)))
            if not complete:
                break
        if not complete:
            break
    targets = list({target['path']: target for target in targets}.values())
    action = 'remove-legacy-gnu-compiler-dumps' if kind == 'dumps' else 'remove-legacy-package-build-caches'
    return dict(schema=1, action=action, complete=complete,
                directories=directories, targets=sorted(targets, key=lambda row: row['path']),
                protectedFiles=blocked, reclaimableBytes=sum(row['bytes'] for row in targets))


def ensure_not_open(paths):
    # Fail closed if the host cannot supply an authoritative open-file snapshot.
    result = subprocess.run(['/usr/sbin/lsof', '-n', '-P', '-F', 'pn'],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=15)
    if result.returncode or result.stderr:
        raise ValueError('complete lsof snapshot required before legacy deletion')
    opened = {line[1:] for line in result.stdout.decode(errors='strict').splitlines() if line.startswith('n/')}
    exact = {str(path) for path in paths}
    directories = tuple(str(path) + '/' for path in paths if path.is_dir())
    if exact.intersection(opened) or directories and any(name.startswith(directories) for name in opened):
        raise ValueError('legacy artifact still open by a live process')


def apply(root, path, expected_sha):
    if digest(path) != expected_sha:
        raise ValueError('plan approval digest mismatch')
    requested = json.loads(path.read_text())
    kinds = {'remove-legacy-gnu-compiler-dumps': 'dumps',
             'remove-legacy-package-build-caches': 'package-caches'}
    kind = kinds.get(requested.get('action'))
    if requested.get('schema') != 1 or kind is None or any(
            row.get('kind') != kind for row in requested['targets']):
        raise ValueError('consistent approved artifact class required')
    with lease(root, exclusive=True):
        protected = protected_paths(root)
        targets = [relative(root, row['path']) for row in requested['targets']]
        for target, row in zip(targets, requested['targets']):
            if (not target.is_relative_to(root / '.data') or root / row['path'] != target or
                target.is_symlink() or intersects(target, protected)):
                raise ValueError('legacy dump identity or protection changed')
            if row['kind'] == 'dumps':
                current = dict(path=row['path'], kind='dumps', **file_identity(target))
                valid = DUMP_NAME.fullmatch(target.name) and target.is_file()
            elif row['kind'] == 'package-caches':
                package = target.parent.parent
                valid = (target.name in ('lib', 'bin') and target.parent.name == '.gerbil' and
                         package.name == 'project' and target.is_dir())
                current = dict(path=row['path'], kind='package-caches',
                    projectPkgSha256=digest(package / 'gerbil.pkg'), **fingerprint(target, deadline=time.monotonic() + 15))
            else:
                raise ValueError('unknown artifact class')
            if not valid or current != row:
                raise ValueError('legacy artifact identity changed')
        if targets:
            ensure_not_open(targets)
        destination = path.with_name(path.stem + '-applied.json')
        if destination.exists():
            raise ValueError('cleanup receipt already exists')
        receipt = dict(schema=1, planSha256=expected_sha, removed=[], state='running')
        atomic_json(destination, receipt)
        try:
            for target, row in zip(targets, requested['targets']):
                if row['kind'] == 'dumps':
                    target.unlink()
                else:
                    shutil.rmtree(target)
                receipt['removed'].append(row)
                atomic_json(destination, receipt)
        finally:
            receipt.update(state='terminal', complete=len(receipt['removed']) == len(targets))
            atomic_json(destination, receipt)
    return receipt
