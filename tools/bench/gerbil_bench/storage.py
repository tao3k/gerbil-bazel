import contextlib
import fcntl
import hashlib
import json
import os
import time
from pathlib import Path


def digest(path):
    with Path(path).open('rb') as source:
        return hashlib.file_digest(source, 'sha256').hexdigest()


def relative(root, value):
    path = Path(value)
    if path.is_absolute():
        raise ValueError('configuration paths must be workspace-relative')
    resolved = (root / path).resolve()
    if not resolved.is_relative_to(root.resolve()) or '..' in path.parts:
        raise ValueError('path escapes workspace')
    return resolved


def atomic_json(path, value):
    temporary = path.with_suffix(path.suffix + '.tmp')
    with temporary.open('w') as output:
        json.dump(value, output, indent=2, sort_keys=True)
        output.write('\n')
        output.flush()
        os.fsync(output.fileno())
    temporary.replace(path)


@contextlib.contextmanager
def lease(root, *, exclusive=False):
    data = root / '.data'
    data.mkdir(exist_ok=True)
    with (data / '.gerbil-bench.lock').open('a') as lock:
        fcntl.flock(lock, (fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH) | fcntl.LOCK_NB)
        try:
            yield
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


def files(path, *, exclude=(), deadline=None):
    """Never traverse links: copied sources and cleanup targets must be self-contained."""
    result = []
    for directory, dirs, names in os.walk(path, followlinks=False):
        if deadline is not None and time.monotonic() >= deadline:
            raise TimeoutError('bounded tree inventory incomplete')
        dirs[:] = [name for name in dirs if name not in exclude]
        names = [name for name in names if name not in exclude]
        for name in dirs + names:
            item = Path(directory) / name
            if item.is_symlink():
                raise ValueError('symlink in managed tree: ' + str(item.relative_to(path)))
        for name in names:
            if deadline is not None and time.monotonic() >= deadline:
                raise TimeoutError('bounded tree inventory incomplete')
            item = Path(directory) / name
            stat = item.stat()
            if not item.is_file():
                raise ValueError('regular files required')
            result.append((str(item.relative_to(path)), stat.st_size, stat.st_mtime_ns))
    return sorted(result)


def fingerprint(path, *, deadline=None):
    entries = files(path, deadline=deadline)
    return dict(bytes=sum(row[1] for row in entries), files=len(entries),
                treeSha256=hashlib.sha256(json.dumps(entries).encode()).hexdigest())
