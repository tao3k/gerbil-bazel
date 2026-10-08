"""Original native import behavior, not an optimization or timing admission."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import time
import sys

from bazel_host_environment import build_environment
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'tools/bench'))
from gerbil_bench.runner import workers as hardware_workers
from gerbil_bench.execution import Budget, execute
from gerbil_bench.storage import atomic_json, lease

EXPECTED_CASES = (
    'initializer-eager', 'initializer-per-context', 'fresh-bindings',
    'same-resolved-source', 'properties-isolated', 'same-id-keeps-prior',
    'initializer-even-if-prior-kept', 'strong-conflict-raises',
    'conflict-initializer-eager', 'conflict-preserves-prior',
    'weak-does-not-replace-strong', 'initializer-error-propagates',
    'initializer-error-before-insertion', 'initializer-restored',
    'export-resolved-again', 'prior-import-keeps-source-binding',
    'initializer-mutation-before-conflict', 'initializer-mutation-preserved',
    'effect-controls-restored',
    'context-nonsymbol-key-live', 'context-nonsymbol-key-eq',
    'context-nonsymbol-rebind-effect', 'marked-key-substitutes-symbol',
    'marked-key-resolves-live', 'gensym-symbolic-hash-after-gc',
    'head-native-macro-returns-original-form', 'head-public-resolver-wrapper-not-reached',
    'head-original-macro-applied-once', 'head-resolver-restored',
    'head-stop-live-predicate-reached', 'head-stop-caller-sees-new-binding',
    'head-stop-new-special-handler-selected', 'head-stop-original-body-preserved',
    'head-stop-predicate-restored',
)

NATIVE_STAGE_CASES = (
    'native-descriptors-returned', 'mapping-defers-c-and-scheme',
    'mapping-records-supplied-but-uninitialized-global', 'descriptor-thunk-survives-gc',
    'zero-stage-preserves-effects', 'stage-one-only-c',
    'stage-one-preserves-scheme-value', 'stage-two-orders-c-before-scheme',
    'stage-two-sets-live-value', 'repeated-init-preserves-identity-and-effects',
    'duplicate-native-map-is-refused',
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--native-stages', action='store_true')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    output = args.output.resolve()
    if output.exists() or not output.is_relative_to(root / '.data'):
        parser.error('fresh persistent .data output required')
    binary = root / '.data/d1510-reader-whitespace-native-v2/gerbil'
    expected = '1f83878a01744817ceb6e74e5d07138948930a41386e568d156210ce9108bb21'
    if hashlib.sha256(binary.read_bytes()).hexdigest() != expected:
        raise ValueError('retained native host identity changed')
    output.mkdir()
    workers = hardware_workers()
    home = root / '.data/d1510-mcp-test-source-home-v2/build'
    fixture = Path(__file__).with_name(
        'native_stage_contract.scm' if args.native_stages else 'import_binding_contract.scm')
    expected_cases = NATIVE_STAGE_CASES if args.native_stages else EXPECTED_CASES
    fixture_hash = hashlib.sha256(fixture.read_bytes()).hexdigest()
    env = build_environment()
    for key in tuple(env):
        if key.startswith(('GAMBIT_DARWIN_', 'GERBIL_MCP_')):
            env.pop(key)
    env.pop('GERBIL_BUILD_PREFIX', None)
    env.update(GERBIL_HOME=str(home), GERBIL_LOADPATH=str(home / 'lib'),
               GAMBIT_EMBEDDED_NATIVE='0', GERBIL_BUILD_CORES=str(workers))
    compilation = None
    module = output / 'native_stage_module.o1'
    module_hash = None
    if args.native_stages:
        driver = root / '.data/d1510-shell-substitution/bin'
        compiler = subprocess.check_output([str(driver / 'gambuild-C'), 'C_COMPILER'],
                                           env=env, text=True, timeout=5).strip()
        if 'gcc' not in compiler.lower() or 'clang' in compiler.lower():
            raise ValueError('native-stage compilation requires original GNU GCC driver')
        source = Path(__file__).with_name('native_stage_module.scm')
        source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
        private_source = output / source.name
        shutil.copy2(source, private_source)
        if hashlib.sha256(private_source.read_bytes()).hexdigest() != source_hash:
            raise ValueError('native-stage source changed during copying')
        env.update(GAMBOPT=f'~~bin={driver},~~lib={home / "lib"},~~include={home / "include"}')
        with lease(root):
            compilation = execute([str(driver / 'gsc'), '-o', str(module), str(private_source)],
                                  output, env, output / 'compile.log', Budget(30))
        compilation.pop('command', None)
        if not compilation['passed'] or not module.is_file():
            atomic_json(output / 'report.json', dict(passed=False, compilation=compilation,
                        performanceQualified=False, productionAdmitted=False))
            raise SystemExit(1)
        module_hash = hashlib.sha256(module.read_bytes()).hexdigest()
        compilation.update(sourceSha256=source_hash,
                           moduleSha256=module_hash, compiler=compiler,
                           driverSha256=hashlib.sha256((driver / 'gambuild-C').read_bytes()).hexdigest())
    started = time.monotonic()
    budget = Budget(20, 5)
    def run(index):
        job = output / str(index)
        job.mkdir()
        (job / 'gxi').symlink_to(binary)
        (job / 'package-home').mkdir()
        (job / 'tmp').mkdir()
        local = dict(env, GERBIL_PATH=str(job / 'package-home'), TMPDIR=str(job / 'tmp'))
        if args.native_stages:
            local.update(NATIVE_STAGE_MODULE=str(module), NATIVE_STAGE_MARKER=str(job / 'stages.txt'))
        row = execute([str(job / 'gxi'), '-e', '(load ' + json.dumps(str(fixture)) + ')'],
                      job, local, job / 'original.log', budget)
        # Absolute fixture paths remain only in private logs, not shareable receipts.
        row.pop('command', None)
        text = (job / 'original.log').read_text(errors='replace')
        cases = [line.split('\t', 1)[1] for line in text.splitlines()
                 if line.startswith('IMPORT-BINDING-CASE\t')]
        row.update(index=index, cases=cases)
        row['passed'] = (row['passed'] and '*** ERROR' not in text and tuple(cases) == expected_cases and
                        text.rstrip().endswith(f'IMPORT-BINDING-OK\t{len(expected_cases)}'))
        return row
    with lease(root), ThreadPoolExecutor(max_workers=workers) as pool:
        rows = list(pool.map(run, range(workers)))
    unchanged = hashlib.sha256(binary.read_bytes()).hexdigest() == expected
    fixture_unchanged = hashlib.sha256(fixture.read_bytes()).hexdigest() == fixture_hash
    module_unchanged = module_hash is None or hashlib.sha256(module.read_bytes()).hexdigest() == module_hash
    source_unchanged = module_hash is None or all(hashlib.sha256(path.read_bytes()).hexdigest() == source_hash
                                                 for path in (source, private_source))
    passed = (all(row['passed'] for row in rows) and unchanged and fixture_unchanged
              and module_unchanged and source_unchanged)
    report = dict(scope=('original-native-stage-contract' if args.native_stages else
                         'original-native-import-binding-contract'), passed=passed,
                  workers=workers, casesPerProcess=len(expected_cases), runs=rows,
                  wallSeconds=time.monotonic() - started, binarySha256=expected,
                  binaryUnchanged=unchanged, consumerPackages=[],
                  fixtureSha256=fixture_hash, fixtureUnchanged=fixture_unchanged,
                  compilation=compilation, moduleUnchanged=module_unchanged,
                  moduleSourceUnchanged=source_unchanged,
                  performanceQualified=False, productionAdmitted=False)
    atomic_json(output / 'report.json', report)
    print(json.dumps(dict(passed=passed, workers=workers, casesPerProcess=len(expected_cases),
                          totalCases=sum(len(row['cases']) for row in rows), binaryUnchanged=unchanged,
                          fixtureUnchanged=fixture_unchanged, performanceQualified=False)), flush=True)
    if not passed:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
