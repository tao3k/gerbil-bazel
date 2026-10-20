"""Verify actual native load selection after an isolated standard-library build."""
import argparse
import json
from pathlib import Path

from bazel_host_environment import build_environment
from native_object_manifest import digest
from progressive_performance_gate import Limits
from experiment_framework.context import data_path, retained_47
from experiment_framework.process import execute


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--attempt', type=int, default=1)
    args = parser.parse_args()
    if args.attempt < 1:
        parser.error('positive attempt required')
    root = Path(__file__).resolve().parents[3]
    output = data_path(root, args.output)
    report = json.loads((output / 'report.json').read_text())
    binary = (output / 'bin/gxi').resolve()
    if not report['qualified'] or digest(binary) != report['binarySha256']:
        raise ValueError('qualified unchanged construction required')
    project = output / 'project'
    lib = project / 'artifacts/lib'
    toolchain = retained_47(root, binary)
    env = toolchain.environment(build_environment(), package_home=output / 'package-home',
                                load_paths=[lib, toolchain.home / 'lib'],
                                workers=report['hardwareWorkers'], bin_dir=output / 'bin')
    expression = '''(begin (import :std/list/list :std/encoding/json/api)
      (for-each (lambda (entry)
        (when (string? (cdr entry))
          (display "ARTIFACT\\t") (write (car entry)) (display "\\t")
          (write (cdr entry)) (newline))) (list-modules)) (displayln "OK"))'''
    suffix = '' if args.attempt == 1 else f'-v{args.attempt}'
    log = output / f'artifact-load{suffix}.log'
    receipt = output / f'artifact-verification{suffix}.json'
    if log.exists() or receipt.exists():
        raise ValueError('fresh verification attempt required')
    result = execute([str(output / 'bin/gxi'), '-e', expression], project, env,
                     log, Limits('artifact-selection', complete=20, first=None))
    lines = log.read_text().splitlines()
    loaded = dict((json.loads(parts[1]), json.loads(parts[2]))
                  for line in lines if line.startswith('ARTIFACT\t')
                  for parts in [line.split('\t')])
    expected = ('std/list/list~0', 'std/encoding/json/reader~0',
                'std/encoding/json/writer~0')
    selected = {key: loaded.get(key) for key in expected}
    qualified = result['passed'] and lines[-1:] == ['OK'] and all(
        path and Path(path).is_relative_to(lib) and Path(path).is_file()
        for path in selected.values())
    evidence = dict(scope='actual-native-artifact-selection-not-full-suite',
                    qualified=qualified, selected=selected, execution=result,
                    constructionReportSha256=digest(output / 'report.json'),
                    binaryUnchanged=digest(binary) == report['binarySha256'])
    evidence['qualified'] &= evidence['binaryUnchanged']
    receipt.write_text(json.dumps(evidence, indent=2) + '\n')
    print(json.dumps(evidence), flush=True)
    return 0 if evidence['qualified'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
