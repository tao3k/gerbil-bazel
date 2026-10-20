import hashlib
import json
import math
from pathlib import Path


STACK = Path(__file__).resolve().parent.parent


def test_preflight_locks_all_referenced_evidence():
    from experiment_framework.patch_lock import verify_patch_lock

    path = STACK / 'receipts/d1510-mcp-v4-patch-lock.json'
    lock = json.loads(path.read_text())
    assert set(lock['receiptFiles']) == {
        lock['runtimePrerequisite'], lock['performancePolicy'], lock['measuredCheckpoint'],
    }
    assert lock['sourceFiles'] == {'gambit-file-sha256.c': lock['nativeDigestSourceSha256']}
    assert verify_patch_lock(path) == 5


def test_measured_patch_series_is_content_locked():
    lock = json.loads((STACK / 'receipts/d1510-mcp-v4-patch-lock.json').read_text())
    series = (STACK / lock['series']).read_text().splitlines()
    assert series == list(lock['patches'])
    assert len(series) == 5 and len(set(series)) == 5
    for name in series:
        assert Path(name).name == name
        assert hashlib.sha256((STACK / name).read_bytes()).hexdigest() == lock['patches'][name]
    assert lock['defaultEnabled'] is False
    checkpoint = json.loads((STACK / 'receipts' / lock['measuredCheckpoint']).read_text())
    assert lock['helperSha256'] == checkpoint['helperSha256']
    assert lock['nativeDigestSourceSha256'] == checkpoint['nativeDigestSourceSha256']
    assert lock['driverFiles'] == {
        'gambuild-C': checkpoint['driverSha256'],
        'gambit-static-object-reuse': checkpoint['helperSha256'],
        'gambit-file-sha256': checkpoint['nativeDigestSha256'],
    }


def test_new_performance_policy_does_not_rewrite_historical_receipt():
    lock = json.loads((STACK / 'receipts/d1510-mcp-v4-patch-lock.json').read_text())
    current = json.loads((STACK / 'receipts' / lock['performancePolicy']).read_text())
    checkpoint = json.loads((STACK / 'receipts' / lock['measuredCheckpoint']).read_text())
    assert current['limitsSeconds'] == dict(firstLog=4.5, completeBuild=42, completeTest=97)
    assert checkpoint['gates'] == dict(firstCompileSeconds=5, completeBuildSeconds=50, completeTestSeconds=112)
    assert current['candidateBinarySha256'] == checkpoint['binarySha256']
    assert current['completeTest']['passingSamples'] == 1


def test_runtime_and_native_source_match_measured_stack():
    lock = json.loads((STACK / 'receipts/d1510-mcp-v4-patch-lock.json').read_text())
    checkpoint = json.loads((STACK / 'receipts' / lock['measuredCheckpoint']).read_text())
    runtime = json.loads((STACK / 'receipts' / lock['runtimePrerequisite']).read_text())
    assert runtime['candidateBinarySha256'] == checkpoint['binarySha256']
    assert lock['runtimeFiles'] == {'gerbil': checkpoint['binarySha256']}
    assert hashlib.sha256((STACK / 'tests/gambit-file-sha256.c').read_bytes()).hexdigest() == lock['nativeDigestSourceSha256']
    assert lock['patches'][checkpoint['patch']] == checkpoint['patchSha256']


def test_performance_lock_preserves_all_measured_samples():
    current = json.loads((STACK / 'receipts/d1510-mcp-v4-performance-lock.json').read_text())
    checkpoint = json.loads((STACK / 'receipts' / current['baselineReceipt']).read_text())
    assert current['coldSamples'] == [
        dict(firstCompileSeconds=sample['firstCompileSeconds'],
             buildWallSeconds=sample['completeBuildSeconds'])
        for sample in checkpoint['coldSamples']
    ]
    observed = checkpoint['observed']
    assert math.isclose(current['completeTest']['wallSeconds'], observed['completeTestSeconds'], abs_tol=1e-9)
    assert current['completeTest']['files'] == observed['passedFiles'] == observed['files'] == 39
    assert current['completeTest']['cases'] == observed['passedCases'] == observed['cases'] == 965
    assert current['completeTest']['passed'] is True
    raw = checkpoint['rawReceipts']
    patch_lock = json.loads((STACK / 'receipts/d1510-mcp-v4-patch-lock.json').read_text())
    assert patch_lock['rawEvidenceFiles'] == {
        name: raw[name] for name in (
            '.data/d1510-static-reuse-mcp-v4/report.json',
            '.data/d1510-static-reuse-mcp-v4/tests/report.json',
        )
    }
    assert current['rawColdReceiptSha256'] == raw['.data/d1510-static-reuse-mcp-v4/report.json']
    assert current['rawCompleteTestReceiptSha256'] == raw['.data/d1510-static-reuse-mcp-v4/tests/report.json']


def test_active_ceilings_follow_ten_percent_rounding():
    current = json.loads((STACK / 'receipts/d1510-mcp-v4-performance-lock.json').read_text())
    samples = current['coldSamples']
    assert current['limitsSeconds'] == dict(
        firstLog=math.ceil(max(sample['firstCompileSeconds'] for sample in samples) * 1.1 * 2) / 2,
        completeBuild=math.ceil(max(sample['buildWallSeconds'] for sample in samples) * 1.1),
        completeTest=math.ceil(current['completeTest']['wallSeconds'] * 1.1),
    )


def test_snapshot_candidate_preserves_baseline_and_partial_admission_boundary():
    from experiment_framework.patch_lock import verify_patch_lock

    path = STACK / 'receipts/d1510-static-c-snapshot-patch-lock.json'
    candidate = json.loads(path.read_text())
    baseline = json.loads((STACK / 'receipts/d1510-mcp-v4-patch-lock.json').read_text())
    policy = json.loads((STACK / 'receipts' / baseline['performancePolicy']).read_text())
    assert verify_patch_lock(path) == 6
    assert list(candidate['patches'])[:-1] == list(baseline['patches'])
    for name, digest in baseline['patches'].items():
        assert candidate['patches'][name] == digest
    assert candidate['runtimeFiles'] == baseline['runtimeFiles']
    assert candidate['limitsSeconds'] == policy['limitsSeconds']
    assert candidate['driverFiles']['gambuild-C'] == baseline['driverFiles']['gambuild-C']
    assert candidate['driverFiles']['gambit-file-sha256'] == baseline['driverFiles']['gambit-file-sha256']
    assert candidate['defaultEnabled'] is False and candidate['productionAdmitted'] is False
    assert candidate['mcpQualified'] is True and candidate['ascentCompleteQualified'] is False
    assert candidate['performanceGainAttributed'] is False
    assert len(candidate['coldSamples']) == 3
    for sample in candidate['coldSamples']:
        assert 0 < sample['firstCompileSeconds'] <= policy['limitsSeconds']['firstLog']
        assert 0 < sample['completeBuildSeconds'] <= policy['limitsSeconds']['completeBuild']
    test = candidate['completeTest']
    assert (test['files'], test['cases'], test['passingSamples']) == (39, 965, 1)
    assert 0 < test['wallSeconds'] <= policy['limitsSeconds']['completeTest']
