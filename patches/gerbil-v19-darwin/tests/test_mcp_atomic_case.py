import pytest

from run_mcp_atomic_case import attach_census, atomic_admission


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


def test_interrupted_observer_prefix_never_admits_case(tmp_path):
    (tmp_path / '7.log').write_text('1\t1\tgxi\tloaded\t-\t0\t0\t0\t0\n')
    report = dict(atomicPassed=False, failure='first deadline')
    attach_census(report, tmp_path, 7)
    assert not report['atomicPassed']
    assert report['failure'] == 'first deadline'
    assert report['processCensus']['apiCounts'] == {}
    assert report['processCensus']['observationScope'] == 'terminated-prefix-not-original-case-coverage'
    assert not report['processCensus']['caseCompleted']


def test_missing_root_observer_denies_even_successful_case(tmp_path):
    report = dict(atomicPassed=True)
    attach_census(report, tmp_path, 7)
    assert not report['atomicPassed']
    assert 'actual target observer loading required' in report['processCensusFailure']
