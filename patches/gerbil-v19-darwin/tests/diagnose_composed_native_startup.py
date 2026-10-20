"""Separate runtime readiness from original Native-parent imports; not a speed gate."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

from bazel_host_environment import build_environment
from build_runtime_image_composition import validate_composed_runtime
from run_parser_native_admission_cost import run


NATIVE_SOURCE = 't/fixtures/tla-sany-differential/native-suite.ss'


def diagnostic_expression(stage):
    expression = '(displayln "NATIVE-RUNTIME-READY") (force-output) '
    if stage == 'parent-imports':
        expression += ('(import :std/misc/process :std/os/signal) '
                       '(displayln "NATIVE-PARENT-IMPORTS-READY") (force-output) ')
    elif stage == 'parent-source':
        expression += (f'(load {json.dumps(NATIVE_SOURCE)}) '
                       '(displayln "NATIVE-PARENT-SOURCE-READY") (force-output) ')
    elif stage != 'runtime':
        raise ValueError('unknown diagnostic stage')
    return (expression + '(import :gerbil-parser/t/fixtures/tla-sany-differential/exit-child-process) '
            '(test-child-process-exit! 0)')


def main():
    parser = argparse.ArgumentParser()
    for name in ('baseline', 'candidate', 'build-receipt', 'project', 'output'):
        parser.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    baseline, candidate, receipt, project, output = (path.resolve() for path in
        (args.baseline, args.candidate, args.build_receipt, args.project, args.output))
    if not all(path.is_relative_to(root/'.data') for path in (baseline, candidate, receipt, project, output)):
        parser.error('isolated composition diagnosis required')
    build = json.loads(receipt.read_text())
    validate_composed_runtime(candidate/'build', build, baseline/'build')
    head = subprocess.check_output(['git', '-C', str(project), 'rev-parse', 'HEAD'], text=True).strip()
    source = (project/NATIVE_SOURCE).read_bytes()
    if (head != build['projectHead'] or source != subprocess.check_output(
            ['git', '-C', str(project), 'show', f'{head}:{NATIVE_SOURCE}'])):
        parser.error('original Native parent source identity changed')
    environment = build_environment()
    cores = int(subprocess.check_output(['sysctl', '-n', 'hw.physicalcpu'], text=True))
    output.mkdir(parents=True, exist_ok=False)
    report = dict(qualified=False, performanceQualified=False, diagnosticOnly=True,
                  scope='composed-runtime-readiness-and-native-parent-imports-not-cases', cores=cores,
                  buildReceiptSha256=hashlib.sha256(receipt.read_bytes()).hexdigest(), runs=[],
                  projectHead=head, nativeSourceSha256=hashlib.sha256(source).hexdigest(),
                  wallBudgetSeconds=90, silenceBudgetSeconds=5)
    for role in ('baseline', 'candidate'):
        home = (baseline if role == 'baseline' else candidate)/'build'
        env = dict(environment)
        for key in list(env):
            if key.startswith('GAMBIT_DARWIN_'):
                env.pop(key)
        env.update(GERBIL_HOME=str(home), GERBIL_GSC=str(home/'bin/gsc'), GERBIL_BUILD_CORES=str(cores),
                   GERBIL_PATH=str(project/'.gerbil'),
                   GERBIL_LOADPATH=f"{project/'.gerbil/lib'}:{home/'lib'}:{project}",
                   PATH=f"{home/'bin'}:{environment['PATH']}",
                   GAMBOPT=f"~~bin={home/'bin'},~~lib={home/'lib'},~~include={home/'include'},max-heap=1G,debug=q")
        for stage in ('runtime', 'parent-imports', 'parent-source'):
            expression = diagnostic_expression(stage)
            name = f'{role}-{stage}'
            try:
                result = run([str(home/'bin/gxi'), '-e', expression], project, env, output/f'{name}.log', 90, 5)
                report['runs'].append(dict(role=role, stage=stage, **result))
            except BaseException as error:
                report['runs'].append(dict(role=role, stage=stage, failure=repr(error)))
    report['qualified'] = all('failure' not in row for row in report['runs'])
    (output/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    if not report['qualified']:
        raise RuntimeError('composition diagnosis failed one or more unchanged gates')


if __name__ == '__main__':
    main()
