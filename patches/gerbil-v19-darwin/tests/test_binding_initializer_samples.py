import pytest

from run_binding_initializer_samples import parse_samples


BASE = ('INIT-SAMPLE-COUNT\t53\nINIT-SAMPLE\timport\t0.000001\t0\n'
        'INIT-SAMPLE-RESTORED\n')


def test_complete_sample_without_extrapolation():
    result = parse_samples(BASE)
    assert result['sampledCalls'] == 1
    assert not result['extrapolationQualified']


@pytest.mark.parametrize('text', [BASE.replace('53', '181'),
    BASE.replace('0.000001', '-0.1'), BASE.replace('0.000001', 'nan'),
    BASE.replace('import\t', 'unknown\t'), BASE.replace('INIT-SAMPLE-RESTORED\n', ''),
    BASE + 'INIT-SAMPLE-COUNT\t53\n'])
def test_incomplete_or_invalid_observation_rejected(text):
    with pytest.raises(ValueError):
        parse_samples(text)
