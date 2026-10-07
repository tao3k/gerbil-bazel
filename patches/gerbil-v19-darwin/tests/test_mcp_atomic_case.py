import pytest

from run_mcp_atomic_case import atomic_admission


def test_original_single_case_and_final_ok_are_required():
    assert atomic_admission('CASE-OK target\nHARNESS-OK x\nOK\n', 0, 'target', True)


@pytest.mark.parametrize('text', [
    'HARNESS-OK x\nOK\n',
    'CASE-OK other\nOK\n',
    'CASE-OK target\nCASE-OK target\nOK\n',
    'CASE-OK target\nCASE-OK other\nOK\n',
    'CASE-OK target\nHARNESS-OK x\n',
    'CASE-FAIL target\nCASE-OK target\nOK\n',
    '*** ERROR x\nCASE-OK target\nOK\n',
])
def test_empty_wrong_duplicate_or_failed_case_cannot_pass(text):
    assert not atomic_admission(text, 0, 'target', True)


def test_exit_code_and_unchanged_source_are_required():
    text = 'CASE-OK target\nOK\n'
    assert not atomic_admission(text, 42, 'target', True)
    assert not atomic_admission(text, 0, 'target', False)
