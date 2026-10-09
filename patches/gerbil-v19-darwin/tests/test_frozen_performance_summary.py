import subprocess
import sys
from pathlib import Path

import pytest


STACK = Path(__file__).resolve().parent.parent
CLI = STACK / 'tests/experiment_framework/patch_lock.py'


@pytest.mark.parametrize('lock, build, test', [
    ('d1510-mcp-v4-patch-lock.json', '37.365', '87.409'),
    ('d1510-static-c-snapshot-patch-lock.json', '36.414', '86.924'),
])
def test_validated_retained_performance_is_printed(lock, build, test):
    result = subprocess.run(
        [sys.executable, str(CLI), str(STACK / 'receipts' / lock), '--performance'],
        capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 0, result.stderr
    assert 'RETAINED-PERFORMANCE not-a-new-benchmark' in result.stdout
    assert result.stdout.count('COLD ') == 3
    assert f'build={build}s' in result.stdout
    assert f'FULL-TEST {test}s files=39 cases=965 passing-samples=1' in result.stdout
    assert 'GATES first=4.5s build=42s test=97s per-sample-no-averaging' in result.stdout
    assert str(Path.home()) not in result.stdout


def test_identity_only_does_not_claim_performance():
    result = subprocess.run(
        [sys.executable, str(CLI), str(STACK / 'receipts/d1510-static-c-snapshot-patch-lock.json')],
        capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 0, result.stderr
    assert 'performance=False' in result.stdout
    assert 'FULL-TEST' not in result.stdout
