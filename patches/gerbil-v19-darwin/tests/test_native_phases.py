import pytest
from experiment_framework.native_phases import read_events, summarize, union_ns


def event(role, start, end):
    return dict(role=role, start=start, end=end, status=0, user=0, system=0)


def test_parallel_union_not_summed_duration():
    assert union_ns([(10, 30), (20, 40), (60, 80)]) == 50


def test_exact_disjoint_stage_partition():
    events = [event('gsc-link', 20, 40), event('gsc-object', 40, 70),
              event('gsc-object', 50, 80), event('gcc-preprocess', 50, 60),
              event('gcc-link', 80, 90)]
    result = summarize(events, 10, 100)
    assert result['roles']['gsc-object']['wallUnionSeconds'] == 40 / 1e9
    assert sum(result['stagesSeconds'].values()) == pytest.approx(result['taskSeconds'])
    assert result['postGenerationObjectCalls'] == 2
    observed = result['stageObservedIntervals']['objectStage']
    assert observed['compilerUnionSeconds'] == 40 / 1e9
    assert observed['outsideCompilerIntervalsSeconds'] == 0


def test_stage_overlap_clips_intervals_without_double_counting():
    events = [event('gsc-other', 15, 25), event('gsc-link', 20, 40),
              event('gsc-object', 45, 70), event('gcc-object', 50, 60),
              event('gcc-link', 80, 90)]
    result = summarize(events, 10, 100)['stageObservedIntervals']
    assert result['preparation']['compilerUnionSeconds'] == 5 / 1e9
    assert result['preparation']['outsideCompilerIntervalsSeconds'] == 5 / 1e9
    assert result['gscLinkGeneration']['compilerUnionSeconds'] == 20 / 1e9
    assert result['objectStage']['compilerUnionSeconds'] == 25 / 1e9
    assert result['objectStage']['outsideCompilerIntervalsSeconds'] == 15 / 1e9


@pytest.mark.parametrize('bad', [
    '1\t1\t2\tgsc-link\t30\t20\t0\t0\t0\n',
    '1\t1\t2\tunknown\t20\t30\t0\t0\t0\n',
    '1\t1\t2\tgsc-link\t20\t30\t0\tNaN\t0\n',
    'truncated\n', '',
    '1\t1\t2\tgsc-link\t20\t30\t0\t0\t0\n' * 2,
])
def test_corrupt_trace_rejected(tmp_path, bad):
    path = tmp_path / 'trace'
    path.write_text(bad)
    with pytest.raises(ValueError):
        read_events(path)


def test_out_of_task_and_missing_phase_rejected():
    with pytest.raises(ValueError):
        summarize([event('gsc-link', 20, 40)], 30, 100)
    with pytest.raises(ValueError):
        summarize([event('gsc-link', 20, 40)], 10, 100)
