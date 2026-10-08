"""Retire generated binary artifacts, preserving failed experiments' text evidence."""
import json
import os
from pathlib import Path
import re
import time

from .dumps import DUMP_NAME, ensure_not_open, file_identity
from .protection import intersects, protected_paths
from .storage import atomic_json, digest, lease, relative


EXPERIMENT = re.compile(r'd\d+[-_].+')
MACHO = {bytes.fromhex(value) for value in (
    'feedface', 'cefaedfe', 'feedfacf', 'cffaedfe', 'cafebabe', 'bebafeca',
    'cafebabf', 'bfbafeca')}


def artifact(path):
    if DUMP_NAME.fullmatch(path.name):
        return 'gnu-dump'
    if (path.suffix not in ('.o', '.a', '.so', '.dylib', '.exe') and
        not re.search(r'\.o\d+$', path.name) and not path.stat().st_mode & 0o111):
        return None
    if path.suffix in ('.ss', '.scm', '.c', '.h', '.py', '.json', '.log', '.txt', '.md', '.sh'):
        return None
    with path.open('rb') as stream:
        magic = stream.read(8)
    if magic[:4] in MACHO:
        return 'macho'
    if magic == b'!<arch>\n':
        return 'object-archive'
    return None


def failed(record):
    return (record.get('decision') == 'DENY' or record.get('passed') is False or
            record.get('qualified') is False) and record.get('productionAdmitted') is not True


def references(root, value):
    result = set()
    if isinstance(value, dict):
        for key, child in value.items():
            result.update(references(root, key))
            result.update(references(root, child))
    elif isinstance(value, list):
        for child in value:
            result.update(references(root, child))
    elif isinstance(value, str):
        prefix = str(root) + '/'
        if value.startswith(prefix):
            value = value[len(prefix):]
        parts = Path(value).parts
        if len(parts) >= 2 and parts[0] == '.data' and EXPERIMENT.fullmatch(parts[1]):
            result.add('.data/' + parts[1])
    return result


def binary_hashes(value):
    result = set()
    if isinstance(value, dict):
        for key, child in value.items():
            if key in ('binarySha256', 'candidateBinarySha256', 'runtimeSha256') and isinstance(child, str):
                result.add(child)
            else:
                result.update(binary_hashes(child))
    elif isinstance(value, list):
        for child in value:
            result.update(binary_hashes(child))
    return result


def plan(root, *, days=7, seconds=30):
    if days < 1 or seconds <= 0:
        raise ValueError('positive age and scan budget required')
    root = root.resolve()
    protected = protected_paths(root)
    started = time.monotonic()
    deadline, cutoff = started + seconds, time.time() - days * 86400
    selections, reports, pending, catalogue, rejected_hashes = {}, {}, [], {}, set()
    complete = True
    for directory in sorted((root / '.data').iterdir()):
        if time.monotonic() >= deadline:
            complete = False
            break
        if not EXPERIMENT.fullmatch(directory.name) or directory.is_symlink() or intersects(directory, protected):
            continue
        report = directory / 'report.json'
        if not report.is_file() or report.is_symlink() or report.stat().st_size > 10_000_000:
            continue
        try:
            record = json.loads(report.read_text())
        except (ValueError, OSError):
            continue
        if record.get('productionAdmitted') is True:
            protected.add(directory)
            continue
        name = str(directory.relative_to(root))
        catalogue[name] = (report, record)
        if failed(record):
            selections[name] = 'failed'
            reports[str(report.relative_to(root))] = digest(report)
            pending.extend(references(root, record))
            rejected_hashes.update(binary_hashes(record))
        elif report.stat().st_mtime < cutoff:
            selections[name] = 'aged'
            reports[str(report.relative_to(root))] = digest(report)
    for name, (report, record) in catalogue.items():
        if binary_hashes(record).intersection(rejected_hashes):
            selections.setdefault(name, 'failed-input')
            reports[str(report.relative_to(root))] = digest(report)
            pending.extend(references(root, record))
    for name in pending:
        if name not in selections:
            selections[name] = 'failed-input'
    catalogue_seconds = time.monotonic() - started
    # Receipt indexing and artifact walking each get a bounded budget.
    deadline = time.monotonic() + seconds
    targets = []
    scanned = []
    # Native construction roots usually hold the largest disposable objects.
    ordered = sorted(selections.items(), key=lambda item: ('native' not in item[0], item[0]))
    for name, reason in ordered:
        if time.monotonic() >= deadline:
            complete = False
            break
        directory = relative(root, name)
        if not directory.is_dir() or root / name != directory or intersects(directory, protected):
            continue
        scanned.append(name)
        for folder, dirs, names in os.walk(directory, followlinks=False):
            current = Path(folder)
            if (current / '.git').exists():
                dirs[:] = []
                continue
            # Preserve checkouts and dependency stores, including native dependencies.
            dirs[:] = sorted(item for item in dirs if item not in ('.git', 'pkg', 'deps') and
                             not (current / item).is_symlink() and not intersects(current / item, protected))
            for filename in sorted(names):
                if time.monotonic() >= deadline or len(targets) >= 50000:
                    complete = False
                    break
                path = current / filename
                if path.is_symlink() or not path.is_file() or intersects(path, protected):
                    continue
                if reason == 'aged' and path.stat().st_mtime >= cutoff:
                    continue
                kind = artifact(path)
                if kind:
                    targets.append(dict(path=str(path.relative_to(root)), kind=kind, reason=reason,
                                        **file_identity(path)))
            if not complete:
                break
        if not complete:
            break
    return dict(schema=1, action='remove-retired-generated-artifacts', complete=complete,
                olderDays=days, reportHashes=reports, targets=targets,
                scannedDirectories=scanned, selectedDirectories=len(selections),
                catalogueSeconds=catalogue_seconds, wallSeconds=time.monotonic() - started,
                reclaimableBytes=sum(row['bytes'] for row in targets))


def apply(root, path, expected_sha):
    root = root.resolve()
    if digest(path) != expected_sha:
        raise ValueError('plan approval digest mismatch')
    record = json.loads(path.read_text())
    if record.get('schema') != 1 or record.get('action') != 'remove-retired-generated-artifacts':
        raise ValueError('retired artifact plan required')
    with lease(root, exclusive=True):
        protected = protected_paths(root)
        for name, sha in record['reportHashes'].items():
            if digest(relative(root, name)) != sha:
                raise ValueError('experiment receipt changed')
        targets = []
        for row in record['targets']:
            target = relative(root, row['path'])
            parents = list(target.parents)
            checkout = any((parent / '.git').exists() for parent in parents
                           if parent.is_relative_to(root / '.data'))
            if (root / row['path'] != target or not target.is_relative_to(root / '.data') or
                checkout or intersects(target, protected) or target.is_symlink() or
                file_identity(target) != {key: row[key] for key in ('bytes', 'mtimeNs', 'inode', 'device')} or
                artifact(target) != row['kind']):
                raise ValueError('retired artifact identity or protection changed')
            targets.append(target)
        if targets:
            ensure_not_open(targets)
        destination = path.with_name(path.stem + '-applied.json')
        if destination.exists():
            raise ValueError('cleanup receipt already exists')
        journal = destination.with_suffix('.jsonl')
        receipt = dict(schema=1, planSha256=expected_sha, state='running', removed=[],
                       journal=str(journal.relative_to(root)))
        atomic_json(destination, receipt)
        try:
            with journal.open('x') as stream:
                for target, row in zip(targets, record['targets']):
                    stream.write(json.dumps(dict(event='intent', path=row['path'])) + '\n')
                    stream.flush()
                    target.unlink()
                    receipt['removed'].append(row)
                    stream.write(json.dumps(dict(event='removed', **row)) + '\n')
                    stream.flush()
                os.fsync(stream.fileno())
        finally:
            receipt.update(state='terminal', complete=len(receipt['removed']) == len(targets),
                           removedLogicalBytes=sum(row['bytes'] for row in receipt['removed']))
            atomic_json(destination, receipt)
    return receipt
