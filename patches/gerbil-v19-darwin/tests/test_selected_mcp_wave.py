from unittest.mock import Mock, patch
import subprocess

from run_selected_mcp_wave import final_test_ok, reap, wave_admission


def test_complete_wave_over_ceiling_is_denied_even_if_every_case_passes():
    result = wave_admission([dict(passed=True)] * 39, 60.174833416)
    assert result['decision'] == 'DENY' and not result['admitted']
    assert result['failures'] == ['complete-test-wave-over-52-second-ceiling-or-invalid-duration']


def test_wave_ceiling_and_correctness_are_independent():
    assert wave_admission([dict(passed=True)] * 39, 52)['admitted']
    assert not wave_admission([dict(passed=True)] * 39, 52.0001)['admitted']
    assert not wave_admission([dict(passed=True)] * 38, 45)['admitted']
    assert not wave_admission([dict(passed=False)] * 39, 45)['admitted']


def test_final_harness_status_not_late_server_stderr():
    assert final_test_ok('HARNESS-OK test\nOK\ngerbil-mcp server started\n')
    assert not final_test_ok('HARNESS-OK test\n')
    assert not final_test_ok('OK\nCASE-FAIL x\n')


def test_terminal_process_is_not_signalled():
    process = Mock(pid=42, returncode=0)
    process.poll.return_value = 0
    with patch('run_selected_mcp_wave.os.killpg') as kill:
        result = reap(process)
    kill.assert_not_called()
    assert result == dict(errors=[], reaped=True, terminalExitCode=0)


def test_group_permission_error_is_recorded_even_if_owned_pid_reaps():
    process = Mock(pid=42, returncode=-15)
    process.poll.side_effect = [None, -15, -15, -15]
    with patch('run_selected_mcp_wave.os.killpg', side_effect=PermissionError('group')):
        result = reap(process)
    process.send_signal.assert_called_once()
    assert result['reaped'] and len(result['errors']) == 1


def test_kill_escalation_follows_unchanged_cleanup_budget():
    process = Mock(pid=42, returncode=-9)
    process.poll.side_effect = [None, None, -9]
    process.wait.side_effect = [subprocess.TimeoutExpired('child', 2), -9]
    with patch('run_selected_mcp_wave.os.killpg') as kill:
        result = reap(process)
    assert kill.call_count == 2
    assert result['reaped'] and result['errors'] == []
