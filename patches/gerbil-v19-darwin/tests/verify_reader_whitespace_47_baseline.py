"""Verify the cold checkpoint while keeping full-test acceptance false."""
import argparse
import hashlib
import json
from pathlib import Path

from summarize_three_time_gates import summarize

ROOT = Path(__file__).resolve().parents[3]
LOCK = ROOT / 'patches/gerbil-v19-darwin/receipts/d1510-reader-whitespace-47-baseline.json'


def main(source_only=False):
    lock = json.loads(LOCK.read_text())
    assert lock['limitsSeconds'] == dict(firstLog=5, completeBuild=50, completeTest=52)
    assert lock['coldQualified'] and lock['testDurationQualified']
    assert not lock['testQualified'] and not lock['productionAdmitted']
    for relative, expected in lock['artifactHashes'].items():
        if source_only and relative.startswith('.data/'):
            continue
        path = ROOT / relative
        assert path.resolve().is_relative_to(ROOT), relative
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected, relative
    if not source_only:
        from verify_reader_batch_50_baseline import main as verify_parent
        verify_parent()
        cold = json.loads((ROOT / lock['coldReport']).read_text())
        tests = json.loads((ROOT / lock['testReport']).read_text())
        summary = summarize(cold, tests)
        assert summary['candidateBinarySha256'] == lock['candidateBinarySha256']
        assert summary['firstLogGate'] == summary['completeColdBuildGate'] == 'ALLOW'
        assert summary['test']['durationGate'] == 'ALLOW'
        assert summary['test']['correctnessGate'] == summary['decision'] == 'DENY'
        assert len(cold['runs']) == len(lock['coldRuns']) == 3
        for row, frozen in zip(cold['runs'], lock['coldRuns']):
            assert row['binarySha256'] == lock['candidateBinarySha256']
            assert row['passed'] and not row.get('performanceStops')
            assert row['cleanExitCode'] == row['buildExitCode'] == row['nativeImagesAfterClean'] == 0
            for key, value in frozen.items():
                assert row[key] == value
        assert tests['waveWallSeconds'] == lock['testWave']['wallSeconds']
        assert summary['test']['passedFiles'] == lock['testWave']['passedFiles'] == 22
        assert summary['test']['deniedFiles'] == lock['testWave']['deniedFiles'] == 17
        semantics = json.loads((ROOT / lock['semanticReport']).read_text())
        assert semantics['binarySha256'] == lock['candidateBinarySha256']
        assert semantics['semanticControlsPassed'] and semantics['exitCode'] == 0
        assert len(semantics['cases']) == len(set(semantics['cases'])) == 45
    result = dict(sourceVerified=True, localEvidenceVerified=not source_only,
                  limitsSeconds=lock['limitsSeconds'], testQualified=False, productionAdmitted=False)
    print(json.dumps(result))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-only', action='store_true')
    main(parser.parse_args().source_only)
