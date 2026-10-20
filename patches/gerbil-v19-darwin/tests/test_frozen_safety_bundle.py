"""Keep the admitted MCP bundle distinct from unqualified experiments."""

import hashlib
import json
from pathlib import Path
import shutil

import pytest

from experiment_framework.patch_lock import verify_patch_lock


STACK = Path(__file__).resolve().parent.parent
LOCK = STACK / 'receipts/d1510-static-c-snapshot-patch-lock.json'
LOCK_SHA256 = 'a6c612404a9b9c6fde63e198ae25d590b814a57c5d628e6fcce203e0fdbe45a2'
PATCHES = [
    '0014-gambit-darwin-native-object-capture.patch',
    '0015-gambit-darwin-literal-build-substitution.patch',
    '0019-gambit-darwin-static-object-reuse-candidate.patch',
    '0020-gambit-darwin-static-object-reuse-hardening.patch',
    '0021-gambit-darwin-native-static-reuse-digests.patch',
    '0026-gambit-darwin-static-c-snapshot-input.patch',
]


def test_frozen_receipt_identity():
    # Timings and tool identities must not drift while patch bytes stay fixed.
    assert hashlib.sha256(LOCK.read_bytes()).hexdigest() == LOCK_SHA256


def test_whole_receipt_pin_is_checked_before_parsing(tmp_path):
    changed = tmp_path / LOCK.name
    changed.write_bytes(b'not even valid JSON')
    with pytest.raises(ValueError, match='Locked digest mismatch'):
        verify_patch_lock(changed, lock_sha256=LOCK_SHA256)


def test_frozen_patch_order_and_bytes():
    lock = json.loads(LOCK.read_text())
    assert list(lock['patches']) == PATCHES
    assert (STACK / lock['series']).read_text().splitlines() == PATCHES
    assert verify_patch_lock(LOCK, performance=True) == len(PATCHES)


def test_frozen_whole_task_gates_and_inventory():
    lock = json.loads(LOCK.read_text())
    assert lock['limitsSeconds'] == dict(
        firstLog=4.5, completeBuild=42, completeTest=97,
    )
    assert len(lock['coldSamples']) == 3
    assert lock['completeTest']['files'] == 39
    assert lock['completeTest']['cases'] == 965
    assert lock['completeTest']['passingSamples'] == 1


def test_component_receipts_do_not_imply_general_release():
    lock = json.loads(LOCK.read_text())
    assert lock['mcpQualified'] is True
    assert lock['defaultEnabled'] is False
    assert lock['productionAdmitted'] is False
    assert lock['ascentCompleteQualified'] is False
    assert lock['performanceGainAttributed'] is False


@pytest.mark.parametrize('identity', ['driver', 'runtime', 'gsc', 'evidence_root'])
def test_real_frozen_bundle_rejects_selected_tool_or_evidence_drift(tmp_path, identity):
    lock = json.loads(LOCK.read_text())
    if identity == 'gsc':
        selected = tmp_path / 'gsc'
        selected.write_bytes(b'unqualified compiler')
    else:
        selected = tmp_path
        field = {
            'driver': 'driverFiles',
            'runtime': 'runtimeFiles',
            'evidence_root': 'rawEvidenceFiles',
        }[identity]
        # Corrupt the first checked identity without copying large native images.
        target = selected / next(iter(lock[field]))
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b'unqualified replacement')
    with pytest.raises(ValueError, match='mismatch'):
        verify_patch_lock(LOCK, performance=True, **{identity: selected})


@pytest.mark.parametrize('mutation', [
    'none', 'patch-bytes', 'missing-patch', 'reordered-series',
    'experimental-patch', 'helper-bytes', 'receipt-bytes',
])
def test_real_frozen_bundle_rejects_contamination(tmp_path, mutation):
    lock = json.loads(LOCK.read_text())
    receipts = tmp_path / 'receipts'
    receipts.mkdir()
    sources = tmp_path / 'tests'
    sources.mkdir()
    copied_lock = receipts / LOCK.name
    shutil.copyfile(LOCK, copied_lock)
    series = tmp_path / lock['series']
    shutil.copyfile(STACK / lock['series'], series)
    for name in lock['patches']:
        shutil.copyfile(STACK / name, tmp_path / name)
    for name in lock['receiptFiles']:
        shutil.copyfile(STACK / 'receipts' / name, receipts / name)
    for name in lock['sourceFiles']:
        shutil.copyfile(STACK / 'tests' / name, sources / name)

    if mutation == 'patch-bytes':
        with (tmp_path / PATCHES[-1]).open('ab') as stream:
            stream.write(b'\nchanged patch\n')
    elif mutation == 'missing-patch':
        (tmp_path / PATCHES[-1]).unlink()
    elif mutation == 'reordered-series':
        series.write_text('\n'.join(reversed(PATCHES)) + '\n')
    elif mutation == 'experimental-patch':
        with series.open('a') as stream:
            stream.write('0041-gambit-darwin-closed-link-member-proofs.patch\n')
    elif mutation == 'helper-bytes':
        (sources / next(iter(lock['sourceFiles']))).write_bytes(b'changed helper')
    elif mutation == 'receipt-bytes':
        (receipts / next(iter(lock['receiptFiles']))).write_bytes(b'changed receipt')

    if mutation == 'none':
        assert verify_patch_lock(copied_lock, performance=True) == len(PATCHES)
    else:
        with pytest.raises(ValueError):
            verify_patch_lock(copied_lock, performance=True)
