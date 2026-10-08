"""Bounded read-only inventory; partial counts never masquerade as total disk use."""
import os
from pathlib import Path
import time


def inventory(root, seconds=15):
    started = time.monotonic()
    data = root / '.data'
    rows = []
    complete = True
    entries = sorted(data.iterdir())
    for entry in entries:
        if time.monotonic() - started >= seconds:
            complete = False
            break
        row = dict(path=str(entry.relative_to(root)), bytes=0, files=0, complete=True,
                   managed=entry.name == 'bench', symlink=entry.is_symlink())
        if entry.is_symlink():
            rows.append(row)
            continue
        if entry.is_file():
            row.update(bytes=entry.stat().st_size, files=1)
        else:
            for directory, dirs, names in os.walk(entry, followlinks=False):
                dirs[:] = [name for name in dirs if not (Path(directory) / name).is_symlink()]
                for name in names:
                    if time.monotonic() - started >= seconds:
                        row['complete'] = complete = False
                        break
                    path = Path(directory) / name
                    if not path.is_symlink():
                        row['bytes'] += path.stat().st_size
                        row['files'] += 1
                if not row['complete']:
                    break
        rows.append(row)
    return dict(schema=1, complete=complete, bytesKind='logical-not-APFS-allocation',
                observedBytes=sum(row['bytes'] for row in rows), entries=rows,
                unvisitedEntries=len(entries) - len(rows), wallSeconds=time.monotonic() - started)
