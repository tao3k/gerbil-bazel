from pathlib import Path
from unittest.mock import Mock, patch
import subprocess
import sys
import time
import pytest

from progressive_performance_gate import (GateViolation, Limits, ProgressiveGate,
                                         force_stop, instrument_cold_controller)


def test_no_first_compile_forces_deny_at_5():
    gate = ProgressiveGate(Limits('build', silence=10), 100)
    gate.check(105)
    with pytest.raises(GateViolation) as error:
        gate.check(105.0001)
    assert error.value.record['reason'] == 'first-real-log-deadline'


def test_unrelated_output_does_not_reset_first_compile_deadline():
    gate = ProgressiveGate(Limits('build', silence=10), 0)
    for now in (1, 2, 3, 4, 5):
        gate.output(now)
    with pytest.raises(GateViolation):
        gate.output(5.5001)


def test_late_first_compile_cannot_rescue_failed_phase():
    gate = ProgressiveGate(Limits('build'), 0)
    with pytest.raises(GateViolation):
        gate.first(5.5001)
    assert gate.first_event is None


def test_continuous_output_cannot_extend_52_seconds():
    gate = ProgressiveGate(Limits('build', silence=10), 0)
    gate.first(5)
    for now in (10, 20, 30, 40, 50, 52):
        gate.output(now)
    with pytest.raises(GateViolation) as error:
        gate.output(52.0001)
    assert error.value.record['reason'] == 'complete-time-deadline'


def test_test_gap_remains_five_seconds():
    gate = ProgressiveGate(Limits('test', silence=5), 0)
    gate.first(0)
    with pytest.raises(GateViolation) as error:
        gate.check(5.1)
    assert error.value.record['reason'] == 'real-output-gap'


def test_stop_is_kill_not_graceful_wait():
    process = Mock(pid=42, returncode=-9)
    process.poll.return_value = -9
    with patch('progressive_performance_gate.os.killpg') as kill:
        result = force_stop(process)
    assert kill.call_args.args[1].name == 'SIGKILL'
    process.wait.assert_called_once_with(timeout=2)
    assert result['reaped']


def test_actual_retained_controller_is_instrumented_fail_closed():
    root = Path(__file__).resolve().parents[3]
    original = (root / '.data/d1395-mcp-runtime-object-ab.py').read_text()
    rewritten = instrument_cold_controller(original)
    compile(rewritten, 'bounded-cold', 'exec')
    assert 'firstCompileCeilingSeconds=5,' in rewritten
    assert 'buildBudgetSeconds=52' in rewritten
    assert 'signal.SIGTERM' not in rewritten
    with pytest.raises(ValueError):
        instrument_cold_controller(original.replace('budget = 30', 'budget = 31'))


def test_tighter_50_second_ceiling_changes_watchdog_and_receipt():
    root = Path(__file__).resolve().parents[3]
    original = (root / '.data/d1395-mcp-runtime-object-ab.py').read_text()
    rewritten = instrument_cold_controller(original, 50)
    compile(rewritten, 'bounded-cold-50', 'exec')
    assert 'buildBudgetSeconds=50, buildPerformanceCeilingSeconds=50' in rewritten
    assert "complete=30 if name == 'clean' else 50" in rewritten
    for bad in (49, 53, 55, True):
        with pytest.raises(ValueError):
            instrument_cold_controller(original, bad)


@pytest.mark.parametrize('value', [0, -1, float('nan'), float('inf'), True])
def test_invalid_deadline_is_rejected(value):
    with pytest.raises(ValueError):
        Limits('build', first=value)


def test_real_owned_process_is_killed_and_reaped_on_deadline():
    process = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)'],
                               start_new_session=True)
    started = time.monotonic()
    gate = ProgressiveGate(Limits('controlled-watchdog-test', first=.05), started)
    try:
        with pytest.raises(GateViolation):
            while True:
                gate.check(time.monotonic())
                time.sleep(.005)
    finally:
        result = force_stop(process)
    assert result['reaped'] and result['terminalExitCode'] == -9
    assert time.monotonic() - started < 1
