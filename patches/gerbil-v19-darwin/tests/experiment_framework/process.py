"""Owned process execution with real-output gates and terminal cleanup."""
import os
import math
from collections import Counter
from pathlib import Path
import selectors
import signal
import subprocess
import threading
import time

from progressive_performance_gate import GateViolation, ProgressiveGate, force_stop


def spawn_events(directory, root_pid):
    """Require actual target observer loading before admitting API counts."""
    counts, durations = Counter(), Counter()
    root_loaded, rows = False, 0
    for path in directory.glob('*.log'):
        parent = int(path.stem)
        for line in path.read_text().splitlines():
            fields = line.split('\t')
            if len(fields) != 9 or fields[3] not in ('loaded', 'fork', 'spawn', 'spawnp'):
                raise ValueError('complete process observer row required')
            start, end = map(float, fields[:2])
            if not (math.isfinite(start) and math.isfinite(end) and 0 <= start <= end):
                raise ValueError('valid process API interval required')
            explicit, bare, status, child = map(int, fields[5:])
            if explicit not in (0, 1) or bare not in (0, 1) or status < 0:
                raise ValueError('valid process API result required')
            rows += 1
            if fields[3] == 'loaded':
                root_loaded |= parent == root_pid
            else:
                counts[fields[3]] += 1
                durations[fields[3]] += end - start
    if not root_loaded:
        raise ValueError('actual target observer loading required; empty counts are not evidence')
    return dict(rootObserverLoaded=True, rows=rows, apiCounts=dict(counts),
                summedApiSeconds=dict(durations), completeDescendantCoverage=False,
                performanceQualified=False)


def record(command, cwd, env, log_path, *, timeout, termination_grace=5):
    """Bound recorder finalization separately from workload admission deadlines."""
    with log_path.open('w') as log:
        child = subprocess.Popen(command, cwd=cwd, env=env, stdout=log,
                                 stderr=subprocess.STDOUT, start_new_session=True)
        try:
            return child.wait(timeout=timeout)
        finally:
            if child.poll() is None:
                try:
                    os.killpg(child.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
                try:
                    child.wait(timeout=termination_grace)
                except subprocess.TimeoutExpired:
                    force_stop(child)


def execute(command, cwd, env, log_path, limits, compile_only=False, shared=None,
            resource_reader=None):
    start = time.monotonic()
    gate, lock = shared or (ProgressiveGate(limits, start), threading.Lock())
    local_first = None
    row = dict(command=[Path(command[0]).name, *command[1:]], passed=False)
    child = subprocess.Popen(command, cwd=cwd, env=env, stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, start_new_session=True)
    selector = selectors.DefaultSelector()
    selector.register(child.stdout, selectors.EVENT_READ)
    pending = b''
    next_resource = start
    if resource_reader is not None:
        row.update(diagnosticOnly=True, performanceQualified=False,
                   resourceScope=getattr(resource_reader, 'scope',
                                         'owned-root-and-reaped-children-not-live-descendants'),
                   resourceSamples=[], resourceErrors=[])
    try:
        with log_path.open('wb') as log:
            while selector.get_map():
                with lock:
                    gate.check(time.monotonic())
                if resource_reader is not None and time.monotonic() >= next_resource:
                    observed = time.monotonic()
                    try:
                        sample = resource_reader(child.pid)
                        row['resourceSamples'].append(dict(elapsedSeconds=observed - start,
                                                           pid=child.pid, **sample))
                    except (OSError, ValueError) as error:
                        row['resourceErrors'].append(dict(elapsedSeconds=observed - start,
                                                         error=str(error)))
                    next_resource = observed + 1
                for key, _ in selector.select(0.02):
                    data = os.read(key.fileobj.fileno(), 65536)
                    if not data:
                        selector.unregister(key.fileobj)
                        continue
                    now = time.monotonic()
                    log.write(data)
                    log.flush()
                    pending += data
                    while b'\n' in pending:
                        line, pending = pending.split(b'\n', 1)
                        if line and (not compile_only or line.startswith(b'... compile ')):
                            with lock:
                                gate.first(now)
                            if local_first is None:
                                local_first = now - start
            child.wait(timeout=1)
            with lock:
                gate.check(time.monotonic())
        row.update(exitCode=child.returncode, firstOutputSeconds=local_first,
                   wallSeconds=time.monotonic() - start,
                   passed=child.returncode == 0 and (not compile_only or local_first is not None))
    except GateViolation as error:
        row.update(performanceStop=error.record)
    finally:
        selector.close()
        if child.poll() is None or 'performanceStop' in row:
            row['cleanup'] = force_stop(child)
        child.stdout.close()
        row['attemptWallSeconds'] = time.monotonic() - start
    return row
