"""Real imported compiler-context serializer feasibility; no cache, restore or speed claim."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

from bazel_host_environment import build_environment
from build_runtime_image_composition import validate_composed_runtime
from run_parser_native_admission_cost import run


def main():
    parser = argparse.ArgumentParser()
    for name in ('baseline', 'candidate', 'build-receipt', 'project', 'output'):
        parser.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    baseline, candidate, receipt, project, output = (path.resolve() for path in
        (args.baseline, args.candidate, args.build_receipt, args.project, args.output))
    if not all(path.is_relative_to(root/'.data') for path in (baseline, candidate, receipt, project, output)):
        parser.error('isolated immutable artifact and diagnostic paths required')
    build = json.loads(receipt.read_text())
    validate_composed_runtime(candidate/'build', build, baseline/'build')
    head = subprocess.check_output(['git', '-C', str(project), 'rev-parse', 'HEAD'], text=True).strip()
    preload = 't/fixtures/tla-sany-differential/preload.ss'
    if head != build['projectHead'] or (project/preload).read_bytes() != subprocess.check_output(
            ['git', '-C', str(project), 'show', f'{head}:{preload}']):
        parser.error('original interface admission helper changed')
    home = candidate/'build'
    environment = build_environment()
    cores = int(subprocess.check_output(['sysctl', '-n', 'hw.physicalcpu'], text=True))
    environment.update(GERBIL_HOME=str(home), GERBIL_GSC=str(home/'bin/gsc'),
                       GERBIL_BUILD_CORES=str(cores), GERBIL_PATH=str(project/'.gerbil'),
                       GERBIL_LOADPATH=f"{project/'.gerbil/lib'}:{home/'lib'}:{project}",
                       PATH=f"{home/'bin'}:{environment['PATH']}",
                       GAMBOPT=f"~~bin={home/'bin'},~~lib={home/'lib'},~~include={home/'include'},max-heap=1G,debug=q")
    fixture = Path(__file__).with_name('gambit-context-serialization-probe.ss')
    expression = (f'(load {json.dumps(preload)}) (prefer-native-interfaces!) '
                  '(preload-module "std/encoding/json") '
                  '(preload-module "std/build-script") '
                  '(preload-module "gerbil-parser/t/fixtures/tla-sany-differential/exit-child-process")')
    output.mkdir(parents=True, exist_ok=False)
    report = dict(qualified=False, performanceQualified=False, diagnosticOnly=True,
                  scope='native-serialization-of-original-compiler-context-no-registry-restore-or-speedup',
                  projectHead=head, cores=cores, wallBudgetSeconds=90, silenceBudgetSeconds=5,
                  fixtureSha256=hashlib.sha256(fixture.read_bytes()).hexdigest(),
                  buildReceiptSha256=hashlib.sha256(receipt.read_bytes()).hexdigest())
    try:
        load_probe = ('(call-with-native-interface-trace (lambda () '
                      f'(load {json.dumps(str(fixture))}) (eval (quote (main)))))')
        report['run'] = run([str(home/'bin/gxi'), '-e', expression, '-e', load_probe], project,
                            environment, output/'probe.log', 90, 5)
        if hashlib.sha256(fixture.read_bytes()).hexdigest() != report['fixtureSha256']:
            raise RuntimeError('diagnostic fixture changed during execution')
        rows = [json.loads(line.removeprefix('SERIALIZATION-PROBE ')) for line in
                (output/'probe.log').read_text().splitlines() if line.startswith('SERIALIZATION-PROBE ')]
        if len(rows) != 1 or rows[0].get('registryRestored') is not False or rows[0].get('diagnosticOnly') is not True:
            raise RuntimeError('exact terminal diagnostic result required; registry changes prohibited')
        report['result'] = rows[0]
        report['qualified'] = True
    except BaseException as error:
        report['failure'] = repr(error)
        raise
    finally:
        (output/'report.json').write_text(json.dumps(report, indent=2)+'\n')


if __name__ == '__main__':
    main()
