"""Verify the three-run cold anchor without admitting the failed test wave."""
import hashlib
import json

from verify_source_loader_49_baseline import ROOT, main as verify_parent

LOCK = ROOT / 'patches/gerbil-v19-darwin/receipts/d1510-reader-batch-50-baseline.json'


def main():
    verify_parent()
    lock = json.loads(LOCK.read_text())
    assert lock['ceilingSeconds'] == 50 and lock['firstCompileCeilingSeconds'] == 5
    assert lock['coldQualified'] is True
    assert lock['testQualified'] is False and lock['productionAdmitted'] is False
    for relative, expected in lock['artifactHashes'].items():
        path = (ROOT / relative).resolve()
        assert path.is_relative_to(ROOT), relative
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected, relative
    report = json.loads((ROOT / lock['coldReport']).read_text())
    assert report['qualified'] and report['sourceUnchanged']
    assert report['buildPerformanceCeilingSeconds'] == 50
    assert len(report['runs']) == len(lock['coldRuns']) == 3
    for row, frozen in zip(report['runs'], lock['coldRuns']):
        assert row['passed'] and row['sourceUnchanged']
        assert row['nativeImagesAfterClean'] == 0
        assert row['binarySha256'] == lock['candidateBinarySha256']
        assert not row.get('performanceStops')
        for key, ceiling in (('firstCompileSeconds', 5), ('buildWallSeconds', 50)):
            assert row[key] == frozen[key] and 0 < row[key] <= ceiling
    tests = json.loads((ROOT / lock['testReport']).read_text())
    assert tests['binarySha256'] == lock['candidateBinarySha256']
    assert not tests['qualified'] and tests['admission']['decision'] == 'DENY'
    assert sum(row['passed'] for row in tests['runs']) == 31
    assert len(tests['runs']) == 39
    latest = json.loads((ROOT / lock['latestGuardReport']).read_text())
    assert lock['latestGuardRunAdmitted'] is False and not latest['qualified']
    row = latest['runs'][0]
    assert not row['passed'] and row['binarySha256'] == lock['candidateBinarySha256']
    assert row['firstCompileSeconds'] <= 5
    assert row['performanceStops'][0]['reason'] == 'complete-time-deadline'
    assert row['performanceStops'][0]['ceilingSeconds'] == 50
    assert row['buildCleanup']['reaped'] and row['buildTerminalExitCode'] == -9
    print(json.dumps(dict(verified=True, ceilingSeconds=50, coldQualified=True,
                          latestGuardRunAdmitted=False,
                          testQualified=False, productionAdmitted=False)))


if __name__ == '__main__':
    main()
