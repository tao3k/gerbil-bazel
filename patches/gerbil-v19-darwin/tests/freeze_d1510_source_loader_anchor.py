"""Seal the measured 43/45-second candidate without claiming test qualification."""
import argparse
import hashlib
import json
from pathlib import Path


def freeze(root):
    base = root / '.data/d1510-outline-current-native'
    native = root / '.data/d1510-source-loader-linked'
    cold = root / '.data/d1510-source-loader-cold-abba'
    original = json.loads((base / 'report.json').read_text())
    candidate = json.loads((native / 'report.json').read_text())
    report = json.loads((cold / 'report.json').read_text())
    admitted = json.loads((cold / 'admission.json').read_text())
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    assert original['qualified'] and candidate['qualified'] and report['qualified']
    assert admitted['admitted'] and admitted['ceilingSeconds'] == 55
    assert sha(base / 'gerbil') == original['binarySha256']
    assert sha(native / 'gerbil') == candidate['binarySha256']
    assert original['inputHashes'] == candidate['inputHashes']
    assert original['inputHashes'] == {p: sha(root / p) for p in original['inputHashes']}
    helpers = ['d1510-source-loader-helper.scm', 'd1510-source-loader-linked.py',
               'd1510-bound-symbol-native.py', 'd1510-source-loader-cold.py',
               'd1510-bound-symbol-cold.py', 'd1510-shell-cold.py',
               'd1395-mcp-runtime-object-ab.py']
    assert sha(root / '.data/d1510-source-loader-helper.scm') == candidate['helperSha256']
    rows = [r for r in report['runs'] if r['role'] == 'candidate']
    assert len(rows) == 2 and all(r['passed'] and r['buildWallSeconds'] <= 55 for r in rows)
    driver = root / '.data/d1510-shell-substitution/bin/gambuild-C'
    assert sha(driver) == admitted['driverSha256']
    return dict(schemaVersion=1, scope='cold-build-anchor-not-complete-test-admission',
        productionAdmitted=False, testQualified=False, ceilingSeconds=55,
        physicalWorkers=report['cores'], compiler='GNU GCC16', multipleVms=False,
        originalBinarySha256=original['binarySha256'], candidateBinarySha256=candidate['binarySha256'],
        driverSha256=sha(driver), inputHashes=original['inputHashes'],
        constructionInputs={'.data/' + p: sha(root / '.data' / p) for p in helpers},
        retainedArtifacts={str(p.relative_to(root)): sha(p) for p in (
            native / 'gerbil', native / 'gerbil-link.c', native / 'gerbil-link.o',
            native / 'gerbil__compiler__driver.scm', native / 'gerbil__compiler__driver.o')},
        coldRuns=[{k:r[k] for k in ('role', 'cleanWallSeconds', 'firstCompileSeconds',
                  'buildWallSeconds', 'binarySha256')} for r in report['runs']])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    result = freeze(root)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k:result[k] for k in ('scope', 'candidateBinarySha256', 'ceilingSeconds', 'testQualified')}))


if __name__ == '__main__':
    main()
