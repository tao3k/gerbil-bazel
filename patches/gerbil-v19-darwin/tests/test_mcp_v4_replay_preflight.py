import hashlib
import json
import shutil
import subprocess
from pathlib import Path

import pytest


STACK = Path(__file__).resolve().parent.parent


@pytest.mark.parametrize('bundle, message', [
    ('snapshot', 'snapshot requires selected GSC'),
    ('experimental', 'unknown bundle'),
])
def test_replay_rejects_unqualified_selection_before_output(tmp_path, bundle, message):
    output = tmp_path / 'must-not-exist'
    result = subprocess.run(
        ['bash', str(STACK / 'tests/check_mcp_v4_patch_replay.sh'),
         'absent-source', 'absent-driver', str(output), 'absent-runtime', '.', bundle],
        capture_output=True, text=True, timeout=5,
    )
    assert result.returncode == 2
    assert message in result.stderr
    assert not output.exists()


@pytest.mark.parametrize('bundle', ['v4', 'snapshot'])
@pytest.mark.parametrize('mutation', ['none', 'drift', 'missing', 'symlink', 'parent-symlink', 'gsc-drift', 'lock-drift'])
def test_replay_requires_raw_evidence_before_creating_output(tmp_path, mutation, bundle):
    # Only shell preflight executes; the source is absent and no native tool launches.
    stack = tmp_path / 'patches/gerbil-v19-darwin'
    tests = stack / 'tests'
    (tests / 'experiment_framework').mkdir(parents=True)
    (stack / 'receipts').mkdir()
    for name in ['check_mcp_v4_patch_replay.sh', 'experiment_framework/patch_lock.py']:
        shutil.copyfile(STACK / 'tests' / name, tests / name)
    lock_name = ('d1510-mcp-v4-patch-lock.json' if bundle == 'v4'
                 else 'd1510-static-c-snapshot-patch-lock.json')
    lock = json.loads((STACK / 'receipts' / lock_name).read_text())
    for name in [lock['series'], *lock['patches']]:
        shutil.copyfile(STACK / name, stack / name)
    for section, directory in [('receiptFiles', 'receipts'), ('sourceFiles', 'tests')]:
        for name in lock[section]:
            shutil.copyfile(STACK / directory / name, stack / directory / name)
    owned = tmp_path / '.data'
    driver = owned / 'driver'
    runtime = owned / 'runtime'
    for section, directory in [('driverFiles', driver), ('runtimeFiles', runtime)]:
        directory.mkdir(parents=True)
        for name in lock[section]:
            data = ('preflight-only ' + name).encode()
            (directory / name).write_bytes(data)
            lock[section][name] = hashlib.sha256(data).hexdigest()
    for name in lock['rawEvidenceFiles']:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        data = b'preflight-only raw evidence'
        path.write_bytes(data)
        lock['rawEvidenceFiles'][name] = hashlib.sha256(data).hexdigest()
    report = tmp_path / next(iter(lock['rawEvidenceFiles']))
    gsc = owned / 'selected-gsc'
    gsc.write_bytes(b'preflight-only selected GSC')
    lock['gscSha256'] = hashlib.sha256(gsc.read_bytes()).hexdigest()
    if mutation == 'drift':
        report.write_bytes(b'changed evidence')
    elif mutation == 'missing':
        report.unlink()
    elif mutation == 'symlink':
        target = report.with_name('target')
        report.rename(target)
        report.symlink_to(target)
    elif mutation == 'parent-symlink':
        parent = report.parent
        target = owned / 'redirected'
        parent.rename(target)
        parent.symlink_to(target, target_is_directory=True)
    elif mutation == 'gsc-drift':
        gsc.write_bytes(b'wrong GSC')
    (stack / 'receipts' / lock_name).write_text(json.dumps(lock))
    # The synthetic tools need their own receipt pin; never change the real pin.
    if bundle == 'snapshot':
        script = tests / 'check_mcp_v4_patch_replay.sh'
        frozen_pin = 'a6c612404a9b9c6fde63e198ae25d590b814a57c5d628e6fcce203e0fdbe45a2'
        fixture_pin = hashlib.sha256((stack / 'receipts' / lock_name).read_bytes()).hexdigest()
        script.write_text(script.read_text().replace(frozen_pin, fixture_pin))
    if mutation == 'lock-drift':
        if bundle != 'snapshot':
            pytest.skip('Whole-receipt pin belongs to the six-patch checkpoint')
        lock['limitsSeconds']['completeBuild'] = 100
        (stack / 'receipts' / lock_name).write_text(json.dumps(lock))
    output = owned / 'receipt'
    result = subprocess.run(
        ['bash', str(tests / 'check_mcp_v4_patch_replay.sh'),
         str(owned / 'absent-source'), str(driver), str(output), str(runtime),
         str(tmp_path), bundle, str(gsc)],
        cwd=tmp_path.parent, capture_output=True, text=True, timeout=5,
    )
    assert result.returncode != 0
    if mutation == 'none':
        assert 'evidence=True' in result.stdout
        assert output.exists()  # Preflight passed; replay rejects the absent source.
    else:
        assert 'PATCH-LOCK-DENY' in result.stderr
        assert not output.exists()
