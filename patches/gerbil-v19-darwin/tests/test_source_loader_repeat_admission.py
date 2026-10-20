import copy

from admit_source_loader_repeat import repeat_admission
import test_d1510_cold_build_admission as historical


def report(seconds):
    value = historical.ColdBuildAdmissionTests().report()
    value['runs'][0]['buildWallSeconds'] = seconds
    return value


def test_target_and_inclusive_ceiling():
    assert repeat_admission(report(50), 'driver')['targetMet']
    result = repeat_admission(report(52), 'driver')
    assert result['admitted'] and not result['targetMet']


def test_each_run_is_checked_without_averaging():
    value = report(43)
    slow = copy.deepcopy(value['runs'][0])
    slow['buildWallSeconds'] = 52.000001
    value['runs'].append(slow)
    assert not repeat_admission(value, 'driver')['admitted']


def test_invalid_duration_or_failed_product_is_denied():
    for seconds in (float('nan'), float('inf'), True, 0, -1):
        assert not repeat_admission(report(seconds), 'driver')['admitted']
    value = report(49)
    value['runs'][0]['buildExitCode'] = 1
    assert not repeat_admission(value, 'driver')['admitted']
