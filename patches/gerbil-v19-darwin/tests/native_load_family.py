"""Bound native-load observations to a real first-compile process family."""
import csv
from collections import defaultdict


def summarize(stream, run, home):
    if not (run['cleanPassed'] and run['nativeImagesAfterClean'] == 0 and
            run['buildPassed'] and run['deliberatelyStoppedAfterFirstCompile']):
        raise ValueError('successful clean and genuine first-compile boundary required')
    start, end = run['buildNativeStartNs'], run['firstCompileNativeNs']
    root = run['buildPid']
    if end <= start:
        raise ValueError('invalid monotonic window')
    events = []
    for fields in csv.reader(stream, delimiter='\t'):
        if len(fields) not in (9, 10):
            raise ValueError('invalid native census row')
        reused = int(fields[9]) if len(fields) == 10 else 0
        if reused not in (0, 1):
            raise ValueError('invalid reuse kind')
        pid, parent, sec, nanos, phase, success = map(int, fields[:6])
        if not 0 <= nanos < 1000000000 or phase not in (0, 1) or success not in (0, 1):
            raise ValueError('invalid native census values')
        timestamp = sec*1000000000+nanos
        if start <= timestamp <= end:
            events.append((timestamp, pid, parent, phase, success, *fields[6:9], reused))
    pending, paths, duration, parents, names = {}, defaultdict(set), defaultdict(int), {}, {}
    native_paths, reuse_paths = defaultdict(set), defaultdict(set)
    for timestamp, pid, parent, phase, success, name, path, linker, reused in events:
        if pid in parents and parents[pid] != parent:
            raise ValueError('process identity changed')
        parents[pid], names[pid] = parent, name
        key = pid, path, linker, reused
        if phase == 0:
            if key in pending:
                raise ValueError('duplicate unmatched load')
            pending[key] = timestamp
        else:
            if key not in pending:
                raise ValueError('unmatched load completion')
            duration[pid] += timestamp-pending.pop(key)
            if success:
                paths[pid].add(path)
                (reuse_paths if reused else native_paths)[pid].add(path)
    if pending:
        raise ValueError('load still pending at first compile')
    family = {root}
    while added := {pid for pid, parent in parents.items() if parent in family}-family:
        family.update(added)
    children = family-{root}
    if set(parents)-family:
        raise ValueError('unrelated process in census window')
    if root not in paths or not any(names[pid] == 'gxi' for pid in children):
        raise ValueError('root and shebang child observations required')
    all_paths = set().union(*(paths[pid] for pid in family))
    child_paths = set().union(*(paths[pid] for pid in children))
    prefix = str(home).rstrip('/')+'/'
    if any(not path.startswith(prefix) for path in all_paths):
        raise ValueError('load outside locked library home')
    relative = lambda values: sorted(path[len(prefix):] for path in values)
    return dict(diagnosticOnly=True, performanceQualified=False,
        scope='completed-native-loads-before-real-first-compile-not-Scheme-cost',
        paths=relative(all_paths), childOnlyPaths=relative(child_paths-paths[root]),
        processes=[dict(pid=pid, parentPid=parents[pid], program=names[pid],
                        successfulUniqueLoads=len(paths[pid]),
                        ordinaryNativeLoads=len(native_paths[pid]),
                        embeddedNativeHits=len(reuse_paths[pid]),
                        observedLoaderSeconds=duration[pid]/1000000000)
                   for pid in sorted(family)])
