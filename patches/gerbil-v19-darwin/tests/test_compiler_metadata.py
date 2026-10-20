import pytest

from experiment_framework.metadata import parse


def test_own_not_inclusive_sum():
    row = parse('METADATA-CALL\t1\tchild\t0.2\t0.2\n'
                'METADATA-CALL\t0\tparent\t0.5\t0.3\n'
                'METADATA-COMPILE-CPU\t0.7\nOK metadata-compile\n')
    assert row['metadataOwnCpu'] == 0.5


def test_worker_identity_is_retained():
    row = parse('METADATA-CALL\t0\t:gerbil/builtin.ssxi.ss\t0.2\t0.2\t(worker 7)\n'
                'METADATA-COMPILE-CPU\t0.7\nOK metadata-compile\n')
    assert row['calls'][0]['worker'] == '(worker 7)'


@pytest.mark.parametrize('text', [
    'METADATA-COMPILE-CPU\tnan\nOK metadata-compile\n',
    'METADATA-COMPILE-CPU\t0.1\n',
    'METADATA-CALL\t0\tpath\t0.1\t0.2\nMETADATA-COMPILE-CPU\t1\nOK metadata-compile\n',
    'METADATA-CALL\t0\tpath\t1\t1\nMETADATA-COMPILE-CPU\t0.1\nOK metadata-compile\n',
    'METADATA-CALL\t1\tpath\t0.1\t0.1\nMETADATA-COMPILE-CPU\t1\nOK metadata-compile\n',
    'METADATA-CALL\t1\tchild\t0.1\t0.1\nMETADATA-CALL\t0\tparent\t0.2\t0.2\nMETADATA-COMPILE-CPU\t1\nOK metadata-compile\n',
])
def test_reject_incomplete_or_impossible(text):
    with pytest.raises(ValueError):
        parse(text)
