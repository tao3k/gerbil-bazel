"""Sparse original initializer CPU observations; never extrapolate to speedup."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import math
from pathlib import Path
import subprocess

from bazel_host_environment import build_environment
from native_object_manifest import digest
from run_parser_native_admission_cost import run
from run_stdlib_import_cost import parse_inventory, parse_phases


def parse_samples(text):
    counts = [int(line.split('\t')[1]) for line in text.splitlines()
              if line.startswith('INIT-SAMPLE-COUNT\t')]
    if len(counts) != 1 or counts[0] <= 0 or text.count('INIT-SAMPLE-RESTORED\n') != 1:
        raise ValueError('one completed census and restoration required')
    rows = []
    for line in text.splitlines():
        if line.startswith('INIT-SAMPLE\t'):
            _, phase, user, system = line.split('\t')
            user, system = float(user), float(system)
            if phase not in ('import', 'eval', 'cached-import', 'cached-eval') or any(
                    not math.isfinite(x) or x < 0 for x in (user, system)):
                raise ValueError('valid original phase and CPU interval required')
            rows.append(dict(phase=phase, userSeconds=user, systemSeconds=system))
    expected_samples = (counts[0] - 53) // 128 + 1 if counts[0] >= 53 else 0
    if len(rows) != expected_samples or not rows:
        raise ValueError('complete deterministic sample sequence required')
    return dict(calls=counts[0], sampledCalls=len(rows), stride=128, offset=53,
                sampledCpuSeconds=sum(r['userSeconds'] + r['systemSeconds'] for r in rows),
                rows=rows, extrapolationQualified=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    output = args.output.resolve()
    if output.exists() or not output.is_relative_to(root / '.data'):
        parser.error('fresh persistent .data output required')
    binary = root / '.data/d1510-reader-whitespace-native-v2/gerbil'
    sha = '1f83878a01744817ceb6e74e5d07138948930a41386e568d156210ce9108bb21'
    if digest(binary) != sha:
        raise ValueError('retained host changed')
    home = root / '.data/d1510-mcp-test-source-home-v2/build'
    env = build_environment()
    for key in tuple(env):
        if key.startswith(('GAMBIT_DARWIN_', 'GERBIL_MCP_')):
            env.pop(key)
    env.pop('GERBIL_BUILD_PREFIX', None)
    cores = int(subprocess.check_output(['sysctl', '-n', 'hw.physicalcpu'], text=True))
    output.mkdir()
    (output / 'gxi').symlink_to(binary)
    (output / 'package-home').mkdir()
    env.update(GERBIL_HOME=str(home), GERBIL_PATH=str(output / 'package-home'),
               GERBIL_LOADPATH=str(home / 'lib'), GAMBIT_EMBEDDED_NATIVE='0',
               GERBIL_BUILD_CORES=str(cores))
    fixtures = [Path(__file__).with_name(name) for name in
                ('stdlib_import_cost.scm', 'binding_initializer_samples.scm')]
    original = json.loads((root / '.data/d1510-stdlib-gambit-eval-split-control-v1/report.json').read_text())
    # Controls are keyed by the library identity, never matched by result position.
    controls = {row['module'].removeprefix(':'): row for row in original['runs']}

    def observe(module):
        folder = output / module.replace('/', '-')
        folder.mkdir()
        expression = '(begin ' + ' '.join('(load ' + json.dumps(str(p)) + ')' for p in fixtures)
        expression += " (run-binding-initializer-samples ':" + module + '))'
        try:
            status = run([str(output / 'gxi'), '-e', expression], folder, env, folder / 'original.log', 20)
            text = (folder / 'original.log').read_text(errors='replace')
            result = dict(module=module, **status, phases=parse_phases(text),
                          inventory=parse_inventory(text), samples=parse_samples(text))
            result['inventoryMatchesOriginal'] = result['inventory'] == controls[module]['inventory']
            result['passed'] = status['exitCode'] == 0 and result['inventoryMatchesOriginal']
            return result
        except (RuntimeError, ValueError) as error:
            return dict(module=module, passed=False, error=str(error))

    with ThreadPoolExecutor(max_workers=cores) as pool:
        rows = list(pool.map(observe, ('std/make', 'std/test', 'std/encoding/json', 'std/list/list')))
    unchanged = digest(binary) == sha
    report = dict(scope='sparse-live-binding-initializer-cpu-not-total-budget',
                  qualified=unchanged and all(row['passed'] for row in rows),
                  binaryUnchanged=unchanged, consumerPackages=[], hardwareWorkers=cores,
                  fixtureHashes={p.name: digest(p) for p in fixtures}, runs=rows,
                  performanceQualified=False, productionAdmitted=False)
    (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'runs'}), flush=True)
    return 0 if report['qualified'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
