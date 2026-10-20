"""Offline native monotonic intervals; never launches a compiler or test."""
import argparse
import csv
import json
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

ROLES = {'gsc-link', 'gsc-object', 'gsc-codegen', 'gsc-other',
         'gcc-query', 'gcc-preprocess', 'gcc-object', 'gcc-link'}


def read_events(path):
    events, seen = [], set()
    with path.open(newline='') as stream:
        for row in csv.reader(stream, delimiter='\t'):
            if len(row) != 9 or row[0] != '1' or row[3] not in ROLES:
                raise ValueError('invalid native interval record')
            pid, parent, start, end, status = map(int, (row[1], row[2], row[4], row[5], row[6]))
            user, system = Decimal(row[7]), Decimal(row[8])
            if (pid <= 0 or parent <= 0 or not 0 < start <= end or not 0 <= status <= 255
                    or not user.is_finite() or not system.is_finite() or min(user, system) < 0
                    or (pid, start) in seen):
                raise ValueError('invalid or duplicated native interval')
            seen.add((pid, start))
            events.append(dict(role=row[3], start=start, end=end, status=status,
                               user=float(user), system=float(system)))
    if not events:
        raise ValueError('nonempty native interval evidence required')
    return events


def union_ns(intervals):
    total, end = 0, 0
    for start, finish in sorted(intervals):
        if finish > end:
            total += finish - max(start, end)
            end = finish
    return total


def summarize(events, begin=None, end=None):
    groups = defaultdict(list)
    for event in events:
        groups[event['role']].append(event)
    result = {'roles': {}, 'failedEvents': sum(event['status'] != 0 for event in events)}
    for role, values in groups.items():
        result['roles'][role] = dict(
            count=len(values), wallUnionSeconds=union_ns((v['start'], v['end']) for v in values) / 1e9,
            summedProcessSeconds=sum(v['end'] - v['start'] for v in values) / 1e9,
            userSeconds=sum(v['user'] for v in values), systemSeconds=sum(v['system'] for v in values))
    # Nested GCC work is already included in the parent GSC intervals and CPU.
    result['nestedRolesNotAdditive'] = True
    if begin is not None or end is not None:
        if begin is None or end is None or not 0 < begin < end:
            raise ValueError('complete monotonic task bounds required')
        if any(v['start'] < begin or v['end'] > end for v in events):
            raise ValueError('native interval outside selected task')
        result['taskSeconds'] = (end - begin) / 1e9
        links = groups['gsc-link']
        if len(links) != 1:
            raise ValueError('single entry GSC link required for stage partition')
        link = links[0]
        objects = [v for v in groups['gsc-object'] if v['start'] >= link['end']]
        if not objects:
            raise ValueError('post-generation object stage required')
        objects_end = max(v['end'] for v in objects)
        finals = [v for v in groups['gcc-link'] if v['start'] >= objects_end]
        if len(finals) != 1:
            raise ValueError('one final compiler link required')
        final = finals[0]
        points = [begin, link['start'], link['end'], final['start'], final['end'], end]
        names = ['preparation', 'gscLinkGeneration', 'objectStage', 'finalCompilerLink', 'casesAndAdmission']
        result['stagesSeconds'] = dict(zip(names, ((b - a) / 1e9 for a, b in zip(points, points[1:]))))
        result['stageObservedIntervals'] = {}
        for name, a, b in zip(names, points, points[1:]):
            clipped = [(max(a, v['start']), min(b, v['end'])) for v in events
                       if v['start'] < b and v['end'] > a]
            observed = union_ns(clipped)
            result['stageObservedIntervals'][name] = dict(
                compilerUnionSeconds=observed / 1e9,
                outsideCompilerIntervalsSeconds=(b - a - observed) / 1e9,
                roles={role: union_ns((max(a, v['start']), min(b, v['end']))
                                     for v in values if v['start'] < b and v['end'] > a) / 1e9
                       for role, values in groups.items()})
        result['postGenerationObjectCalls'] = len(objects)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('trace', type=Path)
    parser.add_argument('--begin', type=Path)
    parser.add_argument('--end', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError('fresh phase summary required')
    result = summarize(read_events(args.trace),
                       int(args.begin.read_text()) if args.begin else None,
                       int(args.end.read_text()) if args.end else None)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
