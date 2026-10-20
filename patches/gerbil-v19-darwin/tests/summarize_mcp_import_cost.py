"""Subtract observed nested calls only; not uninstrumented module self costs."""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import re


def subtract_nested(rows, time_only=False):
    pending, result = [], []
    for row in rows:
        depth = row['depth']
        if type(depth) is not int or depth < 0:
            raise ValueError('nonnegative integer call depth required')
        children = []
        while pending and pending[-1]['depth'] > depth:
            child = pending.pop()
            if child['depth'] != depth + 1:
                raise ValueError('incomplete postorder call tree')
            children.append(child)
        exclusive = dict(row,
            observedSelfSeconds=row['seconds'] - sum(c['seconds'] for c in children),
            observedSelfAllocatedBytes=row['allocatedBytes'] - sum(
                c['allocatedBytes'] for c in children))
        if exclusive['observedSelfAllocatedBytes'] < 0 and not time_only:
            raise ValueError('child allocations exceed parent interval: ' + repr(
                (row['module'], row['allocatedBytes'],
                 sum(c['allocatedBytes'] for c in children), len(children))))
        if time_only:
            exclusive.pop('observedSelfAllocatedBytes')
        result.append(exclusive)
        pending.append(row)
    if any(row['depth'] != 0 for row in pending):
        raise ValueError('missing root completion')
    return result


def portable_name(name):
    if name.startswith('"'):
        value = json.loads(name)
        if '/build/lib/' not in value:
            raise ValueError('module outside selected runtime library')
        return value.split('/build/lib/', 1)[1]
    if name.startswith('('):
        return name
    if re.fullmatch(r':[a-zA-Z0-9_./-]+', name):
        return name
    syntax = re.fullmatch(r'#<syntax #\d+ e: (:[a-zA-Z0-9_./-]+)>', name)
    if syntax:
        return 'syntax:' + syntax.group(1)
    raise ValueError('unexpected module identity')


def summarize(rows, time_only=False):
    groups = defaultdict(lambda: dict(calls=0, observedSelfSeconds=0,
                                     observedSelfAllocatedBytes=0))
    attributed = subtract_nested(rows, time_only)
    for row in attributed:
        group = groups[portable_name(row['module'])]
        group['calls'] += 1
        group['observedSelfSeconds'] += row['observedSelfSeconds']
        if not time_only:
            group['observedSelfAllocatedBytes'] += row['observedSelfAllocatedBytes']
        else:
            group.pop('observedSelfAllocatedBytes', None)
    return sorted([dict(module=name, **group) for name, group in groups.items()],
                  key=lambda row: row['observedSelfSeconds'] if time_only else
                                  row['observedSelfAllocatedBytes'], reverse=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--time-only', action='store_true')
    args = parser.parse_args()
    data = json.loads(args.report.read_text())
    if not data.get('importAttributionQualified'):
        parser.error('completed real import attribution required')
    for row in data['runs']:
        if row.get('importCalls'):
            print(json.dumps(dict(index=row['index'], allocationAttributionQualified=not args.time_only,
                                  topObservedCosts=summarize(row['importCalls'], args.time_only)[:15])))


if __name__ == '__main__':
    main()
