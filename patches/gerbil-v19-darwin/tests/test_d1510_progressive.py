import copy
import pytest

from pathlib import Path
import json

from run_d1510_progressive import cold_admission, candidate_ceiling


def test_frozen_candidate_cannot_return_to_52():
    root = Path(__file__).resolve().parents[3]
    lock = json.loads((root / 'patches/gerbil-v19-darwin/receipts/d1510-reader-batch-50-baseline.json').read_text())
    digest = lock['candidateBinarySha256']
    assert candidate_ceiling(root, digest, None) == 50
    assert candidate_ceiling(root, digest, 50) == 50
    with pytest.raises(ValueError):
        candidate_ceiling(root, digest, 52)
    assert candidate_ceiling(root, 'different-candidate', None) == 50
    with pytest.raises(ValueError):
        candidate_ceiling(root, 'different-candidate', 52)
    old_lock = json.loads((root / 'patches/gerbil-v19-darwin/receipts/d1510-source-loader-49-baseline.json').read_text())
    assert candidate_ceiling(root, old_lock['candidateBinarySha256'], None) == 52


def valid_report():
    return dict(qualified=True, sourceUnchanged=True, runs=[dict(
        firstCompileSeconds=4.8, buildWallSeconds=47.2, passed=True)])


@pytest.mark.parametrize('seconds', [5.000001, 5.2, 5.5])
def test_new_first_log_guard_rejects_old_window(seconds):
    report = valid_report()
    report['runs'][0]['firstCompileSeconds'] = seconds
    assert not cold_admission(report, 50)['admitted']


def test_tighter_gate_accepts_actual_complete_run_only():
    report = valid_report()
    report['runs'][0]['buildWallSeconds'] = 50
    assert cold_admission(report, 50)['admitted']
    assert cold_admission(report, 50)['completeBuildCeilingSeconds'] == 50


@pytest.mark.parametrize('seconds', [50.000001, 51, 52, float('nan'), float('inf'), True])
def test_tighter_gate_cannot_average_away_failed_repeat(seconds):
    report = valid_report()
    row = copy.deepcopy(report['runs'][0])
    row['buildWallSeconds'] = seconds
    report['runs'].append(row)
    assert not cold_admission(report, 50)['admitted']


def test_first_log_failure_is_not_a_complete_build_time():
    report = valid_report()
    report['runs'][0].update(passed=False, performanceStops=[dict(reason='first-real-log-deadline')])
    del report['runs'][0]['buildWallSeconds']
    assert not cold_admission(report, 50)['admitted']


@pytest.mark.parametrize('ceiling', [49, 53, 55, True])
def test_no_arbitrary_gate_widening(ceiling):
    with pytest.raises(ValueError):
        cold_admission(valid_report(), ceiling)
