import os
import sys
import threading
import time
import pytest

from progressive_performance_gate import Limits, ProgressiveGate
from run_stdlib_rebuild import execute, selected_driver, qualify_test_result


def test_incomplete_test_preserves_denial_and_missing_time():
    denied = dict(passed=False, exitCode=-9, wallSeconds=None,
                  performanceStop={'reason': 'first-log'}, attemptWallSeconds=5.01)
    row = qualify_test_result(denied, 'test.ss', [])
    assert row['performanceStop'] == denied['performanceStop']
    assert row['exitCode'] == -9 and row['wallSeconds'] is None
    assert row['cases'] is None and not row['caseVerificationPassed']
    assert not row['passed']


def test_success_status_without_complete_cases_is_denied():
    row = qualify_test_result(dict(passed=True, exitCode=0), 'test.ss', ['OK'])
    assert not row['passed'] and row['cases'] is None


def test_complete_cases_do_not_override_process_denial():
    lines = ['CASE example', 'CASE-OK example', 'OK']
    row = qualify_test_result(dict(passed=False, exitCode=7), 'test.ss', lines)
    assert row['caseVerificationPassed'] and row['cases'] == ['example']
    assert not row['passed'] and row['exitCode'] == 7


def test_driver_override_is_isolated_executable_and_explicit(tmp_path):
    home = tmp_path / '.data' / 'home'
    (home / 'bin').mkdir(parents=True)
    original = home / 'bin' / 'gambuild-C'
    original.write_text('#!/bin/sh\nexit 0\n')
    original.chmod(0o755)
    candidate = tmp_path / '.data' / 'candidate'
    candidate.write_bytes(original.read_bytes())
    candidate.chmod(0o755)
    assert selected_driver(tmp_path, home) == original
    assert selected_driver(tmp_path, home, candidate) == candidate
    candidate.chmod(0o644)
    with pytest.raises(ValueError):
        selected_driver(tmp_path, home, candidate)
    with pytest.raises(ValueError):
        selected_driver(tmp_path, home, tmp_path / 'outside')


def test_success_without_compile_log_is_not_admitted(tmp_path):
    result = execute([sys.executable, '-c', 'pass'], tmp_path, os.environ,
                     tmp_path / 'log', Limits('build', complete=2, first=1), compile_only=True)
    assert result['exitCode'] == 0
    assert not result['passed']


def test_first_compile_log_is_recorded(tmp_path):
    result = execute([sys.executable, '-c', 'print("... compile real-source")'],
                     tmp_path, os.environ, tmp_path / 'log',
                     Limits('build', complete=2, first=1), compile_only=True)
    assert result['passed']
    assert result['firstOutputSeconds'] is not None


def test_shared_first_gate_is_not_per_file_silence(tmp_path):
    started = time.monotonic()
    gate = ProgressiveGate(Limits('wave', complete=2, first=0.01), started)
    gate.first(started)
    result = execute([sys.executable, '-c', 'import time; time.sleep(0.05)'],
                     tmp_path, os.environ, tmp_path / 'log', gate.limits,
                     shared=(gate, threading.Lock()))
    assert result['passed']
    assert result['firstOutputSeconds'] is None
