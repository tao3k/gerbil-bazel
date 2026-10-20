"""Hard runtime gates; only real workload output can advance a phase."""
from dataclasses import dataclass
import math
import json
import os
from pathlib import Path
import signal
import subprocess
import time

PERFORMANCE_LOCK = json.loads((Path(__file__).parent.parent / 'receipts/d1510-mcp-v4-performance-lock.json').read_text())
FIRST_LOG_SECONDS = PERFORMANCE_LOCK['limitsSeconds']['firstLog']
COMPLETE_SECONDS = PERFORMANCE_LOCK['limitsSeconds']['completeBuild']
COMPLETE_TEST_SECONDS = PERFORMANCE_LOCK['limitsSeconds']['completeTest']


class GateViolation(TimeoutError):
    def __init__(self, phase, reason, elapsed, ceiling):
        self.record = dict(decision='DENY', phase=phase, reason=reason,
                           observedElapsedSeconds=elapsed, ceilingSeconds=ceiling)
        super().__init__(f'{phase}: {reason}, elapsed={elapsed:.6f}, ceiling={ceiling}')


@dataclass(frozen=True)
class Limits:
    phase: str
    complete: float = COMPLETE_SECONDS
    first: float | None = FIRST_LOG_SECONDS
    silence: float | None = None

    def __post_init__(self):
        for value in (self.complete, self.first, self.silence):
            if value is not None and (type(value) not in (int, float) or
                                      not math.isfinite(value) or value <= 0):
                raise ValueError('positive finite time limits required')


class ProgressiveGate:
    def __init__(self, limits, started):
        self.limits, self.started, self.last_output = limits, started, started
        self.first_event = None

    def check(self, now):
        elapsed = now - self.started
        if not math.isfinite(elapsed) or elapsed < 0:
            raise ValueError('invalid monotonic clock')
        if self.limits.first is not None and self.first_event is None and elapsed > self.limits.first:
            raise GateViolation(self.limits.phase, 'first-real-log-deadline', elapsed, self.limits.first)
        if elapsed > self.limits.complete:
            raise GateViolation(self.limits.phase, 'complete-time-deadline', elapsed, self.limits.complete)
        if self.limits.silence is not None and now - self.last_output > self.limits.silence:
            raise GateViolation(self.limits.phase, 'real-output-gap', elapsed, self.limits.silence)

    def output(self, now):
        self.check(now)
        self.last_output = now

    def first(self, now):
        self.check(now)
        if self.first_event is None:
            self.first_event = now - self.started


def force_stop(process):
    """Kill the owned session immediately, then reap; never extend admission time."""
    errors = []
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    except PermissionError as error:
        errors.append(repr(error))
        try:
            process.kill()
        except ProcessLookupError:
            pass
        except PermissionError as owned_error:
            errors.append(repr(owned_error))
    try:
        process.wait(timeout=2)
    except subprocess.TimeoutExpired as error:
        errors.append(repr(error))
    return dict(errors=errors, reaped=process.poll() is not None,
                terminalExitCode=process.returncode)


def instrument_cold_controller(source, complete=COMPLETE_SECONDS):
    if type(complete) is not int or not 0 < complete <= COMPLETE_SECONDS:
        raise ValueError('cannot widen the frozen MCP cold-build ceiling')
    replacements = (
        ('55-second complete-build performance ceiling FAILED',
         f'{complete}-second complete-build performance ceiling FAILED'),
        ('buildBudgetSeconds=180, buildPerformanceCeilingSeconds=55,',
         f'buildBudgetSeconds={complete}, buildPerformanceCeilingSeconds={complete}, firstCompileCeilingSeconds={FIRST_LOG_SECONDS},'),
        ("    budget = 30 if name == 'clean' else 180",
         f"    gate = ProgressiveGate(Limits(name, complete=30 if name == 'clean' else {complete}, "
         f"first=None if name == 'clean' else {FIRST_LOG_SECONDS}, silence=None if name == 'clean' else 10), started)"),
        ("                if now - started > budget or (name == 'build' and now - last > 10):\n"
         "                    raise TimeoutError(f'{name}: unchanged real-output/budget gate')",
         '                gate.check(now)'),
        ('                    last = now', '                    gate.output(now)\n                    last = now'),
        ("                        if name == 'build' and line.startswith(b'... compile '):",
         "                        if name == 'build' and line.startswith(b'... compile '):\n"
         '                            gate.first(now)'),
        ('        status = process.wait(timeout=1)',
         '        gate.check(time.monotonic())\n        status = process.wait(timeout=1)'),
        ('    finally:\n        selector.close()',
         "    except GateViolation as error:\n"
         "        row.setdefault('performanceStops', []).append(error.record)\n"
         '        raise\n    finally:\n        selector.close()'),
        ('        if process.poll() is None:\n'
         '            os.killpg(process.pid, signal.SIGTERM)\n'
         '            try:\n                process.wait(timeout=5)\n'
         '            except subprocess.TimeoutExpired:\n'
         '                os.killpg(process.pid, signal.SIGKILL)\n                process.wait()',
         "        if process.poll() is None or row.get('performanceStops'):\n"
         "            row[name + 'Cleanup'] = force_stop(process)\n"
         "        row[name + 'AttemptWallSeconds'] = time.monotonic() - started"),
    )
    for before, after in replacements:
        if source.count(before) != 1:
            raise ValueError('retained controller changed; refusing instrumentation: ' + before[:70])
        source = source.replace(before, after)
    return source
