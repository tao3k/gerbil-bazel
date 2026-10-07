import copy
import pytest

from summarize_three_time_gates import summarize
from run_selected_mcp_wave import wave_admission


def reports():
    cold = dict(runs=[dict(binarySha256='reader', firstCompileSeconds=4.8,
                           buildWallSeconds=47.8, buildExitCode=0, sourceUnchanged=True)
                      for _ in range(3)])
    tests = dict(binarySha256='reader', waveWallSeconds=49.98, expectedCases=965,
                 runs=[dict(passed=True) for _ in range(39)])
    return cold, tests


def test_three_independent_time_gates_and_success():
    cold, tests = reports()
    result = summarize(cold, tests)
    assert result['limitsSeconds'] == dict(firstLog=5, completeBuild=50, completeTest=52)
    assert result['decision'] == 'ALLOW'


def test_49_second_denied_wave_is_not_a_successful_full_test_time():
    cold, tests = reports()
    for row in tests['runs'][:17]:
        row['passed'] = False
    result = summarize(cold, tests)
    assert result['completeColdBuildGate'] == 'ALLOW'
    assert result['test']['durationGate'] == 'ALLOW'
    assert result['test']['correctnessGate'] == 'DENY'
    assert result['test']['successfulCompleteTestSeconds'] is None
    assert result['decision'] == 'DENY'


def test_other_candidate_cannot_override_three_passed_builds():
    cold, tests = reports()
    tests['binarySha256'] = 'fd-archive'
    with pytest.raises(ValueError, match='different candidates'):
        summarize(cold, tests)


@pytest.mark.parametrize('field,value', [('firstCompileSeconds', 5.001),
                                       ('buildWallSeconds', 50.014),
                                       ('buildWallSeconds', None),
                                       ('buildWallSeconds', float('nan')),
                                       ('buildWallSeconds', True)])
def test_failed_round_cannot_be_averaged_away(field, value):
    cold, tests = reports()
    cold['runs'][1][field] = value
    assert summarize(cold, tests)['decision'] == 'DENY'


def test_test_51_seconds_passes_52_gate_without_changing_build_gate():
    cold, tests = reports()
    tests['waveWallSeconds'] = 51
    assert summarize(cold, tests)['decision'] == 'ALLOW'
    cold['runs'][0]['buildWallSeconds'] = 51
    assert summarize(cold, tests)['decision'] == 'DENY'


def test_interrupted_build_has_no_complete_time_and_no_test_receipt():
    cold, _ = reports()
    row = copy.deepcopy(cold['runs'][0])
    del row['buildWallSeconds']
    row['buildExitCode'] = -9
    result = summarize(dict(runs=[row]))
    assert result['coldRuns'][0]['completeBuildSeconds'] is None
    assert result['test']['durationGate'] == 'SKIP'
    assert result['firstLogGate'] == 'ALLOW'
    assert result['coldRepeatGate'] == 'INCOMPLETE'
    assert result['decision'] == 'DENY'


def test_real_wave_uses_52_seconds_without_conflating_correctness():
    rows = [dict(passed=True) for _ in range(39)]
    assert wave_admission(rows, 51)['admitted']
    assert not wave_admission(rows, 52.001)['durationGatePassed']
    rows[0]['passed'] = False
    result = wave_admission(rows, 49)
    assert result['durationGatePassed'] and result['targetMet']
    assert not result['correctnessGatePassed'] and not result['admitted']
