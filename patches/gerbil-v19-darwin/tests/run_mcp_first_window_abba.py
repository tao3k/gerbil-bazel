"""Official unchanged MCP clean/build first-window ABBA; never a full-build pass."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import sys

from build_runtime_image_composition import validate_composed_runtime


def paired_first_window(runs):
    if [row.get('role') for row in runs] != ['baseline', 'candidate', 'candidate', 'baseline']:
        raise ValueError('complete original-order ABBA required')
    first = {}
    for role in ('baseline', 'candidate'):
        values = [row['observation'].get('firstCompileSeconds') for row in runs if row['role'] == role]
        if any(type(value) not in (int, float) or not math.isfinite(value) or value <= 0 for value in values):
            raise ValueError('every actual first compile must be observed')
        first[role] = sum(values)/len(values)
    return dict(baselineMeanSeconds=first['baseline'], candidateMeanSeconds=first['candidate'],
                ratio=first['baseline']/first['candidate'],
                reductionPercent=100*(1-first['candidate']/first['baseline']))


def main():
    parser = argparse.ArgumentParser()
    for name in ('baseline', 'candidate', 'image-receipt', 'project', 'output'):
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--head', required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    baseline, candidate, receipt, project, output = (path.resolve() for path in
        (args.baseline, args.candidate, args.image_receipt, args.project, args.output))
    if not all(path.is_relative_to(root/'.data') for path in (baseline, candidate, receipt, project, output)):
        parser.error('durable isolated source and observations required')
    build = json.loads(receipt.read_text())
    validate_composed_runtime(candidate/'build', build, baseline/'build')
    if hashlib.sha256((baseline/'build/bin/gxi').read_bytes()).hexdigest() != build['originalRuntimeSha256']:
        parser.error('original runtime reference changed')
    output.mkdir(parents=True, exist_ok=False)
    report = dict(qualified=False, performanceQualified=False, diagnosticOnly=True,
                  scope='official-mcp-first-compile-abba-not-complete-build', runs=[],
                  imageBuildReceiptSha256=hashlib.sha256(receipt.read_bytes()).hexdigest(),
                  projectHead=args.head, productOutputGapSeconds=10, buildCompleted=False)
    observer = Path(__file__).with_name('sample_mcp_first_compile.py')
    try:
        for index, role in enumerate(('baseline', 'candidate', 'candidate', 'baseline')):
            source = baseline if role == 'baseline' else candidate
            directory = output/f'{index}-{role}'
            command = [sys.executable, str(observer), '--project', str(project), '--source', str(source),
                       '--head', args.head, '--observe-first-only', '--output', str(directory)]
            if role == 'candidate':
                command += ['--image-receipt', str(receipt)]
            with (output/f'{index}-{role}.supervisor.log').open('w') as log:
                child = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
                try:
                    child.wait(timeout=150)
                finally:
                    if child.poll() is None:
                        os.killpg(child.pid, signal.SIGTERM)
                        try:
                            child.wait(timeout=5)
                        except subprocess.TimeoutExpired:
                            os.killpg(child.pid, signal.SIGKILL)
                            child.wait()
            record = dict(index=index, role=role, supervisorExitCode=child.returncode, hostLoad=os.getloadavg())
            if (directory/'report.json').is_file():
                record['observation'] = json.loads((directory/'report.json').read_text())
            else:
                record['failure'] = 'observation did not produce its terminal receipt'
            report['runs'].append(record)
            observation = record.get('observation', {})
            print(f'MCP-FIRST-WINDOW role={role} first={observation.get("firstCompileSeconds")} '
                  f'gate-failed={observation.get("strictOutputGateFailed")}', flush=True)
        report['pairedFirstCompileDiagnostic'] = paired_first_window(report['runs'])
        if any(row['supervisorExitCode'] != 0 or row['observation'].get('officialCleanPassed') is not True
               or row['observation'].get('buildDeliberatelyStoppedAfterFirstCompile') is not True
               or row['observation'].get('strictOutputGateFailed') is not False for row in report['runs']):
            raise RuntimeError('actual official first-window progress gates failed; paired times are diagnostic only')
        report['qualified'] = True
    except BaseException as error:
        report['failure'] = repr(error)
        raise
    finally:
        (output/'report.json').write_text(json.dumps(report, indent=2)+'\n')


if __name__ == '__main__':
    main()
