import pytest

from experiment_framework.native_receipt import read_compile_failure_receipt


ERROR = 'Incomplete form, EOF reached'


def receipt(root, status=70, extra='', error=ERROR):
    path = root / 'run'
    path.mkdir()
    (path / 'output.log').write_text(f'Syntax Error: {error}\n{extra}')
    (path / 'exit-status.txt').write_text(f'{status}\n')
    (path / 'time.txt').write_text('real 1.0\nuser 0.7\nsys 0.1\n')
    return path


def test_typed_compile_rejection_is_not_a_test_pass(tmp_path):
    result = read_compile_failure_receipt(tmp_path, receipt(tmp_path), ERROR)
    assert result['failureRejected']
    assert not result['correctnessPassed']
    assert result['cases'] == result['casesStarted'] == 0


@pytest.mark.parametrize('status', [0, 124, 125, 126, 127, 137, -15])
def test_timeout_signal_or_success_cannot_qualify_rejection(tmp_path, status):
    result = read_compile_failure_receipt(tmp_path, receipt(tmp_path, status=status), ERROR)
    assert not result['failureRejected']


@pytest.mark.parametrize('extra', [
    'CASE stale executable ran\n', 'CASE-OK stale executable ran\n', 'OK\n',
    'HARNESS-OK stale test\n', 'SUITE-OK stale suite\n', 'MODULE-OK stale module\n',
    'NATIVE-ENTRY-CACHE-HIT\n',
])
def test_old_entry_execution_or_success_markers_are_rejected(tmp_path, extra):
    result = read_compile_failure_receipt(tmp_path, receipt(tmp_path, extra=extra), ERROR)
    assert not result['failureRejected']


def test_unrelated_error_is_not_admitted(tmp_path):
    result = read_compile_failure_receipt(tmp_path, receipt(tmp_path, error='missing compiler'), ERROR)
    assert not result['failureRejected']


def test_specific_error_is_required(tmp_path):
    with pytest.raises(ValueError):
        read_compile_failure_receipt(tmp_path, receipt(tmp_path), ' ')
