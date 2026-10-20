"""Export the exact tested candidate patch and a path-redacted checkpoint."""
import difflib
import argparse
import hashlib
import json
from pathlib import Path

from prepare_static_reuse_driver import inject, native_hash


def diff(path, before, after):
    old = 'a/' + path if before else '/dev/null'
    return ('diff --git a/' + path + ' b/' + path + '\n' +
            ('new file mode 100644\n' if not before else '') +
            ''.join(difflib.unified_diff(before.splitlines(keepends=True),
                                        after.splitlines(keepends=True),
                                        fromfile=old, tofile='b/' + path, n=1)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--revision', choices=('2', '3', '4'), default='2')
    args = parser.parse_args()
    revision = args.revision
    root = Path(__file__).resolve().parents[3]
    directory = root / 'patches/gerbil-v19-darwin'
    original = root / '.data/d1391-runtime-object-source/src/gambit/bin'
    tested = root / f'.data/d1510-static-reuse-driver-v{revision}/bin'
    helper_name = ('gambit-static-object-reuse.unix' if revision == '2'
                   else 'gambit-static-object-reuse-v3.unix')
    helper = Path(__file__).with_name(helper_name).read_bytes()
    if revision == '4':
        helper = native_hash(helper.decode()).encode()
    if helper != (tested / 'gambit-static-object-reuse').read_bytes():
        raise ValueError('only the exact tested helper may be frozen')
    driver = (original / 'gambuild-C.unix.in').read_text()
    make = (original / 'makefile.in').read_text()
    altered = make
    edits = {
        'DISTFILES = $(RCFILES) $(GENDISTFILES)\n':
            'RCFILES += gambit-static-object-reuse.unix\n\nDISTFILES = $(RCFILES) $(GENDISTFILES)\n',
        'INSTFILES_BIN = $(INSTFILES_BIN_PROG) $(INSTFILES_BIN_LINK)\n':
            'INSTFILES_BIN_PROG += gambit-static-object-reuse\n\nINSTFILES_BIN = $(INSTFILES_BIN_PROG) $(INSTFILES_BIN_LINK)\n',
        'gambvcs@bat@: makefile':
            'core-post: gambit-static-object-reuse\n\ngambit-static-object-reuse: makefile $(srcdirpfx)gambit-static-object-reuse.unix\n'
            '\tcp $(srcdirpfx)gambit-static-object-reuse.unix gambit-static-object-reuse\n'
            '\tchmod +x gambit-static-object-reuse\n\ngambvcs@bat@: makefile',
    }
    for anchor, replacement in edits.items():
        if altered.count(anchor) != 1:
            raise ValueError('installation anchor drift')
        altered = altered.replace(anchor, replacement, 1)
    patch = ('Subject: [EXPERIMENTAL PATCH] gambit: opt-in Darwin static object reuse\n\n'
             'Freeze the exact v2 helper tested by the MCP 40.042s cold build and\n'
             '91.040s complete 39-file/965-case test run. Not default-enabled;\n'
             'the cold run had zero reuse hits and is not a causal speedup proof.\n'
             'Repeated cold and real ASCENT admission remain pending.\n\n' +
             diff('bin/gambuild-C.unix.in', driver, inject(driver)) +
             diff('bin/makefile.in', make, altered) +
             diff('bin/gambit-static-object-reuse.unix', '', helper.decode()))
    if revision == '3':
        patch = ('Subject: [EXPERIMENTAL PATCH] gambit: harden opt-in static reuse\n\n'
                 'Apply after 0019. Reject incomplete digests and changed tool/source\n'
                 'snapshots; reject non-regular proof targets; retain the original\n'
                 'compiler path for calls with diagnostics or auxiliary outputs.\n'
                 'This candidate remains default-off pending second-consumer admission.\n\n' +
                 diff('bin/gambit-static-object-reuse.unix',
                      Path(__file__).with_name('gambit-static-object-reuse.unix').read_text(),
                      helper.decode()))
    if revision == '4':
        native_make = altered.replace('RCFILES += gambit-static-object-reuse.unix',
            'RCFILES += gambit-static-object-reuse.unix gambit-file-sha256.c', 1)
        native_make = native_make.replace('INSTFILES_BIN_PROG += gambit-static-object-reuse',
            'INSTFILES_BIN_PROG += gambit-static-object-reuse gambit-file-sha256', 1)
        native_make = native_make.replace('core-post: gambit-static-object-reuse\n',
            'core-post: gambit-static-object-reuse gambit-file-sha256\n\n'
            'gambit-file-sha256: makefile $(srcdirpfx)gambit-file-sha256.c\n'
            '\t$(C_COMPILER) $(FLAGS_EXE) -O2 -Wno-deprecated-declarations $(srcdirpfx)gambit-file-sha256.c -o gambit-file-sha256\n', 1)
        patch = ('Subject: [EXPERIMENTAL DARWIN PATCH] gambit: native static reuse digests\n\n'
                 'Apply after 0020 on Darwin/GNU only. Keep full content identity\n'
                 'while using public CommonCrypto SHA256 instead of repeated Perl\n'
                 'hash processes. Bind the digest executable into the tool snapshot.\n'
                 'Explicit non-Darwin opt-in uses the original command without locks.\n'
                 'Default-off; full second-consumer admission remains incomplete.\n\n' +
                 diff('bin/gambit-static-object-reuse.unix',
                      Path(__file__).with_name(helper_name).read_text(), helper.decode()) +
                 diff('bin/makefile.in', altered, native_make) +
                 diff('bin/gambit-file-sha256.c', '',
                      Path(__file__).with_name('gambit-file-sha256.c').read_text()))
    patch_path = directory / ('0019-gambit-darwin-static-object-reuse-candidate.patch'
                             if revision == '2' else
                             ('0020-gambit-darwin-static-object-reuse-hardening.patch'
                              if revision == '3' else
                              '0021-gambit-darwin-native-static-reuse-digests.patch'))
    patch_path.write_text(patch)
    cold_path = root / f'.data/d1510-static-reuse-mcp-cold-v{revision}/report.json'
    test_revision = '1' if revision == '2' else revision
    test_path = root / f'.data/d1510-static-reuse-mcp-tests-v{test_revision}/report.json'
    if revision == '4':
        cold_path = root / '.data/d1510-static-reuse-mcp-v4/report.json'
        test_path = root / '.data/d1510-static-reuse-mcp-v4/tests/report.json'
    cold, tests = (json.loads(p.read_text()) for p in (cold_path, test_path))
    build = cold['runs'][0]
    cases = sum(row['caseOkCount'] for row in tests['runs'])
    if not (build['passed'] and tests['qualified'] and len(tests['runs']) == 39
            and cases == 965 and all(row['passed'] and row['finalOk'] and
                                   row['inventoryMatches'] for row in tests['runs'])):
        raise ValueError('complete original consumer receipts required')
    receipt = dict(schema=1, status='experimental-candidate-checkpoint',
                   defaultEnabled=False, productionAdmitted=False,
                   repeatedColdQualified=False, ascentQualified=False,
                   performanceGainAttributed=False, observedColdReuseHits=0,
                   patch=patch_path.name,
                   patchSha256=hashlib.sha256(patch_path.read_bytes()).hexdigest(),
                   helperSha256=hashlib.sha256(helper).hexdigest(),
                   driverSha256=hashlib.sha256((tested / 'gambuild-C').read_bytes()).hexdigest(),
                   binarySha256=build['binarySha256'],
                   gates=dict(firstCompileSeconds=5, completeBuildSeconds=50,
                              completeTestSeconds=112),
                   observed=dict(firstCompileSeconds=build['firstCompileSeconds'],
                                 completeBuildSeconds=build['buildWallSeconds'],
                                 testFirstOutputSeconds=tests['firstOutputSeconds'],
                                 completeTestSeconds=tests['waveWallSeconds'],
                                 files=39, passedFiles=39, cases=cases, passedCases=cases),
                   rawReceipts={str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
                                for p in (cold_path, test_path)})
    if revision == '3':
        confirmation = root / '.data/d1510-static-reuse-mcp-cold-v3-confirm/report.json'
        repeated = json.loads(confirmation.read_text())['runs']
        samples = [build, *repeated]
        if not (len(samples) == 3 and all(row['passed'] and row['sourceUnchanged']
                    and row['firstCompileSeconds'] <= 5 and row['buildWallSeconds'] <= 50
                    for row in samples)):
            raise ValueError('all three cold runs must meet the frozen gates')
        receipt['repeatedColdQualified'] = True
        receipt['coldSamples'] = [dict(firstCompileSeconds=row['firstCompileSeconds'],
                                      completeBuildSeconds=row['buildWallSeconds'])
                                  for row in samples]
        receipt['rawReceipts'][str(confirmation.relative_to(root))] = hashlib.sha256(
            confirmation.read_bytes()).hexdigest()
    if revision == '4':
        samples = cold['runs']
        if not (len(samples) == 3 and all(row['passed'] and row['sourceUnchanged']
                    and row['firstCompileSeconds'] <= 5 and row['buildWallSeconds'] <= 50
                    for row in samples)):
            raise ValueError('all three cold runs must meet the frozen gates')
        receipt['repeatedColdQualified'] = True
        receipt['coldSamples'] = [dict(firstCompileSeconds=row['firstCompileSeconds'],
                                      completeBuildSeconds=row['buildWallSeconds']) for row in samples]
        receipt['nativeDigestSha256'] = hashlib.sha256((tested / 'gambit-file-sha256').read_bytes()).hexdigest()
        receipt['nativeDigestSourceSha256'] = hashlib.sha256(
            Path(__file__).with_name('gambit-file-sha256.c').read_bytes()).hexdigest()
        ascent_path = root / '.data/d1510-static-reuse-ascent-native-v4-summary.json'
        ascent = json.loads(ascent_path.read_text())
        if not ascent['correctnessPassed']:
            raise ValueError('actual native consumer correctness required')
        receipt['ascentObservedScenarios'] = ascent['runs']
        receipt['ascentScenarioPerformanceImproved'] = (
            ascent['runs'][2]['completeSeconds'] < ascent['runs'][0]['completeSeconds'])
        receipt['rawReceipts'][str(ascent_path.relative_to(root))] = hashlib.sha256(
            ascent_path.read_bytes()).hexdigest()
    receipt_name = ('d1510-static-object-reuse-40-checkpoint.json' if revision == '2'
                    else f'd1510-static-object-reuse-v{revision}-checkpoint.json')
    (directory / 'receipts' / receipt_name).write_text(
        json.dumps(receipt, indent=2) + '\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
