"""Reviewed retirement of numbered experiment trees, not retained toolchains."""
import json
import os
from pathlib import Path
import shutil
import tarfile
import time

from .dumps import ensure_not_open, file_identity
from .protection import intersects, protected_paths
from .retired import EXPERIMENT, failed
from .storage import atomic_json, digest, lease, relative


def plan(root, *, days=7, batch=20, completed=False, exclude=()):
    root = root.resolve()
    if days < 1 or not 1 <= batch <= 100:
        raise ValueError('positive age and bounded batch required')
    cutoff = time.time() - days * 86400
    protected = protected_paths(root)
    excluded_roots = set()
    for name in exclude:
        path = relative(root, name)
        if path in (root, root / '.data'):
            protected.add(path)
        elif path.is_relative_to(root / '.data'):
            excluded_roots.add(root / '.data' / path.relative_to(root / '.data').parts[0])
    targets = []
    for path in sorted((root / '.data').iterdir()):
        if (not EXPERIMENT.fullmatch(path.name) or path.is_symlink() or not path.is_dir() or
            path in excluded_roots or intersects(path, protected)):
            continue
        report = path / 'report.json'
        sha, rejected, admitted, finished = None, False, False, False
        if report.is_file() and not report.is_symlink() and report.stat().st_size < 10_000_000:
            try:
                record = json.loads(report.read_text())
                if record.get('state') in ('running', 'preparing', 'pending'):
                    continue
                rejected, admitted = failed(record), record.get('productionAdmitted') is True
                finished = record.get('qualified') is True or record.get('passed') is True
                sha = digest(report)
            except (ValueError, OSError):
                continue
        if admitted:
            continue
        old = path.stat().st_mtime < cutoff and (not report.exists() or report.stat().st_mtime < cutoff)
        if rejected or old or completed and finished:
            reason = 'failed' if rejected else 'completed' if completed and finished else 'aged'
            targets.append(dict(path=str(path.relative_to(root)), reason=reason,
                                reportSha256=sha, **file_identity(path)))
        if len(targets) >= batch:
            break
    return dict(schema=1, action='retire-numbered-experiment-trees', olderDays=days,
                includeCompleted=completed,
                excludedPaths=list(exclude),
                targets=targets, evidencePolicy='archive-top-two-level-text-and-receipts')


def archive_evidence(source, destination):
    suffixes = {'.json', '.jsonl', '.log', '.md', '.txt', '.xml', '.py', '.sh',
                '.ss', '.scm', '.ssi', '.c', '.h', '.patch'}
    paths = []
    for entry in sorted(source.iterdir()):
        if entry.is_symlink():
            continue
        if entry.is_file():
            paths.append(entry)
        elif entry.is_dir() and entry.name not in ('.git', 'project', 'src', 'build', 'lib', 'include', 'pkg', 'deps'):
            paths.extend(path for path in sorted(entry.iterdir()) if path.is_file() and not path.is_symlink())
    with tarfile.open(destination, 'x:gz', dereference=False) as output:
        for path in paths:
            if path.suffix in suffixes:
                output.add(path, arcname=str(path.relative_to(source)), recursive=False)
    with destination.open('rb') as stream:
        os.fsync(stream.fileno())
    return dict(path=destination.name, sha256=digest(destination), bytes=destination.stat().st_size)


def logical_size(source):
    total, count, pending = 0, 0, [source]
    while pending:
        with os.scandir(pending.pop()) as entries:
            for entry in entries:
                if entry.is_symlink():
                    continue
                if entry.is_dir(follow_symlinks=False):
                    pending.append(entry.path)
                elif entry.is_file(follow_symlinks=False):
                    total += entry.stat(follow_symlinks=False).st_size
                    count += 1
    return dict(bytes=total, files=count)


def apply(root, path, expected_sha):
    root = root.resolve()
    if digest(path) != expected_sha:
        raise ValueError('plan approval digest mismatch')
    record = json.loads(path.read_text())
    if record.get('schema') != 1 or record.get('action') != 'retire-numbered-experiment-trees':
        raise ValueError('numbered experiment plan required')
    with lease(root, exclusive=True):
        protected = protected_paths(root)
        targets = []
        for row in record['targets']:
            target = relative(root, row['path'])
            if (target.parent != root / '.data' or root / row['path'] != target or
                not EXPERIMENT.fullmatch(target.name) or target.is_symlink() or
                intersects(target, protected) or not target.is_dir() or
                file_identity(target) != {key: row[key] for key in ('bytes', 'mtimeNs', 'inode', 'device')}):
                raise ValueError('numbered experiment identity or protection changed')
            if row['reportSha256'] is not None and digest(target / 'report.json') != row['reportSha256']:
                raise ValueError('experiment receipt changed')
            targets.append(target)
        if targets:
            ensure_not_open(targets)
        destination = path.with_name(path.stem + '-applied.json')
        if destination.exists():
            raise ValueError('cleanup receipt already exists')
        archives = root / '.data/bench/archives' / path.stem
        archives.mkdir(parents=True, exist_ok=False)
        trash = root / '.data/bench/trash' / path.stem
        trash.mkdir(parents=True, exist_ok=False)
        receipt = dict(schema=1, planSha256=expected_sha, state='running', removed=[],
                       quarantined=[], archives=[], availableBefore=os.statvfs(root).f_bavail * os.statvfs(root).f_frsize)
        atomic_json(destination, receipt)
        try:
            for target, row in zip(targets, record['targets']):
                archive = archive_evidence(target, archives / (target.name + '.tar.gz'))
                archive['path'] = str((archives / archive['path']).relative_to(root))
                receipt['archives'].append(archive)
                atomic_json(destination, receipt)
                size = logical_size(target)
                if file_identity(target) != {key: row[key] for key in ('bytes', 'mtimeNs', 'inode', 'device')}:
                    raise ValueError('experiment changed during evidence archival')
                # Renaming isolates the selected tree before recursive removal.
                moved = trash / target.name
                target.rename(moved)
                receipt['quarantined'].append(str(moved.relative_to(root)))
                atomic_json(destination, receipt)
                shutil.rmtree(moved)
                receipt['removed'].append(dict(path=str(target.relative_to(root)), **size))
                atomic_json(destination, receipt)
                print(json.dumps(dict(removed=str(target.relative_to(root)))), flush=True)
        finally:
            receipt.update(state='terminal', complete=len(receipt['removed']) == len(targets),
                           removedLogicalBytes=sum(row['bytes'] for row in receipt['removed']),
                           availableAfter=os.statvfs(root).f_bavail * os.statvfs(root).f_frsize)
            receipt['observedAvailableDeltaBytes'] = receipt['availableAfter'] - receipt['availableBefore']
            atomic_json(destination, receipt)
    return receipt
