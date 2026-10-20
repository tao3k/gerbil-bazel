import json
from pathlib import Path

from verify_reader_whitespace_47_baseline import LOCK, main


def test_portable_verification_never_claims_local_performance():
    result = main(source_only=True)
    assert result['sourceVerified']
    assert not result['localEvidenceVerified']
    assert not result['testQualified'] and not result['productionAdmitted']


def test_checkpoint_retains_all_three_runs_and_denied_correctness():
    lock = json.loads(LOCK.read_text())
    assert len(lock['coldRuns']) == 3
    assert all(row['buildWallSeconds'] <= 50 and row['firstCompileSeconds'] <= 5
               for row in lock['coldRuns'])
    assert lock['testWave']['wallSeconds'] <= 52
    assert lock['testWave']['passedFiles'] == 22 and lock['testWave']['deniedFiles'] == 17
    assert lock['testWave']['decision'] == 'DENY'


def test_reproduction_does_not_import_rejected_span_or_fd_components():
    source = Path(__file__).with_name('build_reader_whitespace_runtime.py').read_text()
    assert 'prepare_darwin_reader_span' not in source
    assert 'fork_fd' not in source and "choices=('span'" not in source
    controls = Path(__file__).with_name('run_reader_whitespace_controls.py').read_text()
    assert 'reader_span' not in controls and 'expected_cases = 45' in controls
