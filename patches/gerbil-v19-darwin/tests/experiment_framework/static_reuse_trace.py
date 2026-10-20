"""Compare retained static-proof component hashes without running native tests."""

import argparse
import json
import re
from pathlib import Path


FIELDS = {'source', 'cpp', 'environment', 'tools', 'command-cwd', 'key'}


def read_traces(directory):
    if directory.is_symlink() or not directory.is_dir():
        raise ValueError('Trace root must be a non-symlink directory')
    traces = {}
    for path in sorted(directory.glob('*.gambit-static-key-trace')):
        if path.is_symlink() or not path.is_file():
            raise ValueError(f'Invalid trace file: {path.name}')
        fields = {}
        for line in path.read_text().splitlines():
            match = re.fullmatch(r'([a-z-]+) ([0-9a-f]{64})', line)
            if not match or match[1] in fields:
                raise ValueError(f'Invalid trace fields: {path.name}')
            fields[match[1]] = match[2]
        if set(fields) != FIELDS:
            raise ValueError(f'Incomplete trace fields: {path.name}')
        traces[path.name] = fields
    if not traces:
        raise ValueError('No static-proof traces')
    return traces


def compare_traces(before, after):
    left, right = read_traces(before), read_traces(after)
    if left.keys() != right.keys():
        raise ValueError('Trace inventories differ')
    changes = {
        name: sorted(field for field in FIELDS if left[name][field] != right[name][field])
        for name in left
    }
    return dict(objects=len(left), changedCounts={
        field: sum(field in fields for fields in changes.values()) for field in sorted(FIELDS)
    }, changes=changes)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('before', type=Path)
    parser.add_argument('after', type=Path)
    args = parser.parse_args()
    try:
        result = compare_traces(args.before, args.after)
    except (OSError, ValueError) as error:
        parser.exit(1, f'STATIC-TRACE-DENY {error}\n')
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == '__main__':
    main()
