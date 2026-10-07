from progressive_performance_gate import Limits, ProgressiveGate, GateViolation
from run_complete_mcp_wave import wave_admission, final_test_ok, execution_limits
import pytest


def test_whole_task_silence_does_not_stop_legitimate_work():
    gate = ProgressiveGate(execution_limits(False), 0)
    gate.first(2)
    gate.check(111)
    with pytest.raises(GateViolation):
        gate.check(112.001)


def test_first_log_still_has_hard_five_second_deadline():
    gate = ProgressiveGate(Limits('whole-test', complete=52, first=5, silence=None), 0)
    with pytest.raises(GateViolation):
        gate.first(5.001)


def test_partial_pass_is_never_complete_acceptance():
    assert not wave_admission([dict(passed=True)] * 36, 49)['admitted']
    assert not wave_admission([dict(passed=True)] * 38 + [dict(passed=False)], 49)['admitted']
    assert wave_admission([dict(passed=True)] * 39, 112)['admitted']
    assert not wave_admission([dict(passed=True)] * 39, 112.001)['admitted']
    assert not wave_admission([dict(passed=True)] * 39, 125)['admitted']


def test_final_ok_cannot_hide_later_failure():
    assert final_test_ok('CASE-OK a\nOK\n')
    assert not final_test_ok('OK\nCASE-FAIL a\n')


def test_completion_diagnostic_does_not_widen_performance_admission():
    gate = ProgressiveGate(execution_limits(True), 0)
    gate.first(6)
    gate.check(130)
    assert not wave_admission([dict(passed=True)] * 39, 130)['admitted']
    with pytest.raises(GateViolation):
        gate.check(900.001)
    assert execution_limits(False).complete == 112
    assert execution_limits(False).first == 5
