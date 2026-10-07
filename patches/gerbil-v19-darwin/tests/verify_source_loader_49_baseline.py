"""Verify the retained local 49-second candidate; never imply test admission."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
LOCK = ROOT / 'patches/gerbil-v19-darwin/receipts/d1510-source-loader-49-baseline.json'


def main():
    lock = json.loads(LOCK.read_text())
    assert lock['ceilingSeconds'] == 52 and lock['targetSeconds'] == 50
    assert lock['productionAdmitted'] is False and lock['testQualified'] is False
    for group in ('inputHashes', 'retainedArtifacts', 'gitArtifactHashes',
                  'retainedReplayInputs'):
        for relative, expected in lock[group].items():
            path = (ROOT / relative).resolve()
            assert path.is_relative_to(ROOT), relative
            assert hashlib.sha256(path.read_bytes()).hexdigest() == expected, relative
    for relative, key in (
        ('.data/d1510-outline-current-native/gerbil', 'originalBinarySha256'),
        ('.data/d1510-source-loader-linked/gerbil', 'candidateBinarySha256'),
        ('.data/d1510-shell-substitution/bin/gambuild-C', 'driverSha256'),
    ):
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == lock[key]
    candidates = [row for row in lock['coldRuns'] if row['role'] == 'candidate']
    assert len(candidates) == 2
    for row in candidates:
        assert row['passed'] and row['sourceUnchanged']
        assert row['nativeImagesAfterClean'] == 0
        assert 0 < row['buildWallSeconds'] <= lock['targetSeconds']
        assert row['binarySha256'] == lock['candidateBinarySha256']
    assert lock['selectedToolchainValidated']
    print(json.dumps(dict(verified=True, ceilingSeconds=52,
                          candidateSeconds=[r['buildWallSeconds'] for r in candidates],
                          testQualified=False, productionAdmitted=False)))


if __name__ == '__main__':
    main()
