import copy
import pytest

from pathlib import Path
import json

from run_d1510_progressive import cold_admission, candidate_ceiling


def test_frozen_candidate_cannot_return_to_52():
    root = Path(__file__).resolve().parents[3]
    lock = json.loads((root / 'patches/gerbil-v19-darwin/receipts/d1510-reader-batch-50-baseline.json').read_text())
    digest = lock['candidateBinarySha256']
    assert candidate_ceiling(root, digest, None) == 42
    assert candidate_ceiling(root, digest, 42) == 42
    with pytest.raises(ValueError):
        candidate_ceiling(root, digest, 52)
    assert candidate_ceiling(root, 'different-candidate', None) == 42
    with pytest.raises(ValueError):
        candidate_ceiling(root, 'different-candidate', 52)
    old_lock = json.loads((root / 'patches/gerbil-v19-darwin/receipts/d1510-source-loader-49-baseline.json').read_text())
    assert candidate_ceiling(root, old_lock['candidateBinarySha256'], None) == 42


def valid_report():
    return dict(qualified=True, sourceUnchanged=True, runs=[dict(
        firstCompileSeconds=4.4, buildWallSeconds=37.2, passed=True)])


@pytest.mark.parametrize('seconds', [4.500001, 5.000001, 5.2, 5.5])
def test_new_first_log_guard_rejects_old_window(seconds):
    report = valid_report()
    report['runs'][0]['firstCompileSeconds'] = seconds
    assert not cold_admission(report, 42)['admitted']


def test_tighter_gate_accepts_actual_complete_run_only():
    report = valid_report()
    report['runs'][0]['buildWallSeconds'] = 42
    assert cold_admission(report, 42)['admitted']
    assert cold_admission(report, 42)['completeBuildCeilingSeconds'] == 42


@pytest.mark.parametrize('seconds', [42.000001, 45, 50, 51, 52, float('nan'), float('inf'), True])
def test_tighter_gate_cannot_average_away_failed_repeat(seconds):
    report = valid_report()
    row = copy.deepcopy(report['runs'][0])
    row['buildWallSeconds'] = seconds
    report['runs'].append(row)
    assert not cold_admission(report, 42)['admitted']


def test_first_log_failure_is_not_a_complete_build_time():
    report = valid_report()
    report['runs'][0].update(passed=False, performanceStops=[dict(reason='first-real-log-deadline')])
    del report['runs'][0]['buildWallSeconds']
    assert not cold_admission(report, 42)['admitted']


@pytest.mark.parametrize('ceiling', [49, 53, 55, True])
def test_no_arbitrary_gate_widening(ceiling):
    with pytest.raises(ValueError):
        cold_admission(valid_report(), ceiling)


def test_locked_three_cold_samples_pass_current_policy():
    root = Path(__file__).resolve().parents[3]
    lock = json.loads((root / 'patches/gerbil-v19-darwin/receipts/d1510-mcp-v4-performance-lock.json').read_text())
    report = dict(qualified=True, sourceUnchanged=True,
                  runs=[dict(sample, passed=True) for sample in lock['coldSamples']])
    assert len(report['runs']) == 3
    assert cold_admission(report)['admitted']
    assert lock['limitsSeconds'] == dict(firstLog=4.5, completeBuild=42, completeTest=97)
