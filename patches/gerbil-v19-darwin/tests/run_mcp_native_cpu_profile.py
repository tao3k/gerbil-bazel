"""Record unchanged real MCP preparation with Instruments CPU Profiler."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time
import xml.etree.ElementTree as ET

from bazel_host_environment import build_environment
from run_parser_native_admission_cost import native_admission_expression
from macho_image_dependencies import validate_packed_image_inventory


def candidate_provenance_valid(runtime, binary_digest, gsc_digest):
    return (runtime.get('qualified') is True and runtime.get('diagnosticOnly') is False
            and runtime.get('gscUnchanged') is True
            and runtime.get('consumerFlagsChanged') is False
            and runtime.get('runtimeAbiChanged') is False
            and runtime.get('binaryHashes', {}).get('gxi') == binary_digest
            and runtime.get('binaryHashes', {}).get('gsc') == gsc_digest)


def native_admission_receipt_valid(previous):
    return (previous.get('qualified') is True and previous.get('diagnosticOnly') is True
            and previous.get('performanceQualified') is False
            and previous.get('scope') == 'referenced-native-batch-preload-prefix-not-case-or-full-suite'
            and previous.get('projectHead') == 'f35b14193db7cfc89444b0f9a82b81c3862bc795'
            and previous.get('nativeExitPolicy') is True
            and previous.get('wallBudgetSeconds') == 90 and previous.get('silenceBudgetSeconds') == 5
            and [row.get('name') for row in previous.get('runs', [])] == ['baseline', 'observer']
            and all(row.get('exitCode') == 0 for row in previous.get('runs', [])))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--expression-receipt', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--binary', type=Path)
    parser.add_argument('--runtime-receipt', type=Path)
    parser.add_argument('--native-admission-project', type=Path)
    parser.add_argument('--native-image-receipt', type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    baseline, receipt, output = (p.resolve() for p in (args.baseline, args.expression_receipt, args.output))
    if not all(p.is_relative_to(root / '.data') for p in (baseline, receipt, output)):
        parser.error('isolated project-data inputs/output required')
    previous = json.loads(receipt.read_text())
    binary = baseline / 'build/bin/gxi'
    digest = hashlib.sha256(binary.read_bytes()).hexdigest()
    project = None
    if args.native_admission_project:
        project = args.native_admission_project.resolve()
        if (not project.is_relative_to(root / '.data') or not native_admission_receipt_valid(previous)
                or args.binary or args.runtime_receipt
                or digest != 'cc3b58b627c25c3844249aa752a7773a53d76e319a0212e90a7f28ee46e21928'):
            parser.error('qualified isolated Native prefix and unchanged original runtime required')
        head = subprocess.check_output(['git', '-C', str(project), 'rev-parse', 'HEAD'], text=True).strip()
        if head != previous['projectHead'] or any(
                hashlib.sha256((project / name).read_bytes()).hexdigest() != expected
                for name, expected in previous['sourceSha256'].items()):
            parser.error('referenced Native source changed')
    else:
        if not previous.get('qualified') or not previous.get('preparationImports'):
            parser.error('completed real preparation expression receipt required')
        if previous['binaryHashes']['baseline'] != digest:
            parser.error('original runtime binary drifted')
    if bool(args.binary) != bool(args.runtime_receipt):
        parser.error('candidate binary requires its completed native build receipt')
    if args.binary:
        binary, runtime_receipt = args.binary.resolve(), args.runtime_receipt.resolve()
        if not all(p.is_relative_to(root / '.data') for p in (binary, runtime_receipt)):
            parser.error('isolated candidate binary and receipt required')
        runtime = json.loads(runtime_receipt.read_text())
        digest = hashlib.sha256(binary.read_bytes()).hexdigest()
        gsc_digest = hashlib.sha256((baseline / 'build/bin/gsc').read_bytes()).hexdigest()
        if not candidate_provenance_valid(runtime, digest, gsc_digest):
            parser.error('candidate provenance or unchanged compiler/ABI gate failed')
    image_receipt = None
    if args.native_image_receipt:
        image_receipt = args.native_image_receipt.resolve()
        if not project or not image_receipt.is_relative_to(root / '.data'):
            parser.error('Native image receipt requires isolated Native mode')
        image_build = json.loads(image_receipt.read_text())
        if (image_build.get('qualified') is not True or image_build.get('binaryHashesUnchanged') is not True
                or image_build.get('originalGambitMacroInputsUsed') is not True
                or image_build.get('scope') != 'current-staging-native-preload-image-packing-prototype'
                or image_build.get('runtimeAbiChanged') is not False
                or image_build.get('consumerFlagsChanged') is not False
                or (root / image_build['candidate']).resolve() != baseline
                or image_build['projectHead'] != previous['projectHead']
                or hashlib.sha256((baseline / 'build/bin/gsc').read_bytes()).hexdigest() != image_build['gscSha256']
                or any(hashlib.sha256((baseline / 'build' / row['path']).with_suffix('.scm').read_bytes()).hexdigest()
                       != row['sourceSha256'] for row in image_build['units'])):
            parser.error('current Native image prototype provenance changed')
        validate_packed_image_inventory(baseline / 'build', image_build)
    output.mkdir(parents=True, exist_ok=False)
    home = baseline / 'build'
    env = build_environment()
    env.update(GERBIL_HOME=str(home), GERBIL_LOADPATH=str(home / 'lib'),
               GERBIL_GSC=str(home / 'bin/gsc'), GERBIL_PATH=str(output / 'empty-user'),
               GAMBOPT=f"~~bin={home / 'bin'},~~lib={home / 'lib'},~~include={home / 'include'}")
    for key in list(env):
        if key.startswith('GAMBIT_') and key != 'GAMBITDIR_INCLUDE':
            env.pop(key)
    if project:
        env.update(GERBIL_PATH=str(project / '.gerbil'),
                   GERBIL_LOADPATH=f"{project / '.gerbil/lib'}:{home / 'lib'}:{project}",
                   GERBIL_BUILD_CORES=str(previous['cores']), GERBIL_PARSER_LR_TRACE='1')
        env['GAMBOPT'] += ',max-heap=1G,debug=q'
    expression = native_admission_expression(project) if project else previous['expression']
    (output / 'expression.ss').write_text(expression + '\n')
    command = ['xcrun', 'xctrace', 'record', '--template', 'CPU Profiler',
               '--output', str(output / 'profile.trace'), '--time-limit', '120s',
               '--no-prompt', '--target-stdout', str(output / 'target.log')]
    keys = ['GERBIL_HOME', 'GERBIL_LOADPATH', 'GERBIL_GSC', 'GERBIL_PATH', 'GAMBOPT']
    if project:
        keys += ['GERBIL_BUILD_CORES', 'GERBIL_PARSER_LR_TRACE']
    for key in keys:
        command.extend(['--env', f'{key}={env[key]}'])
    command.extend(['--launch', '--', str(binary), '-e', expression])
    report = dict(qualified=False, performanceQualified=False,
                  scope='unchanged-runtime-native-CPU-profiler-diagnostic',
                  binarySha256=digest, expressionReceiptSha256=hashlib.sha256(receipt.read_bytes()).hexdigest(),
                  hostLoadStart=os.getloadavg())
    if args.binary:
        report['scope'] = 'existing-uninstrumented-candidate-native-CPU-profiler-diagnostic'
        report['runtimeReceiptSha256'] = hashlib.sha256(runtime_receipt.read_bytes()).hexdigest()
    if project:
        report.update(scope='referenced-native-preload-unchanged-runtime-CPU-profiler-diagnostic',
                      projectHead=previous['projectHead'], nativeSuiteQualified=False)
    if image_receipt:
        report.update(scope='referenced-native-preload-packed-images-unchanged-runtime-CPU-profiler-diagnostic',
                      imageBuildReceiptSha256=hashlib.sha256(image_receipt.read_bytes()).hexdigest())
    started = time.monotonic()
    try:
        with (output / 'profiler.log').open('w') as log:
            child = subprocess.Popen(command, env=env, stdout=log, stderr=subprocess.STDOUT,
                                     start_new_session=True)
            try:
                while child.poll() is None:
                    try:
                        child.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        target = output / 'target.log'
                        size = target.stat().st_size if target.exists() else 0
                        print(f'CPU-PROFILE-OBSERVED target-bytes={size} elapsed={time.monotonic()-started:.1f}s', flush=True)
                    if child.poll() is None and time.monotonic()-started > 180:
                        raise TimeoutError('bounded CPU recording exceeded 180 seconds')
            finally:
                if child.poll() is None:
                    os.killpg(child.pid, signal.SIGTERM)
                    try:
                        child.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        os.killpg(child.pid, signal.SIGKILL)
                        child.wait()
        report['profilerExitCode'] = child.returncode
        if child.returncode:
            raise RuntimeError('CPU Profiler recording failed; inspect retained log')
        content = (output / 'target.log').read_text()
        report['preparedModules'] = sum(line.startswith('PREPARED ') for line in content.splitlines())
        if project:
            report['admittedInterfaces'] = sum(line.startswith('MODULE-IMPORTED ') for line in content.splitlines())
            output_valid = (report['admittedInterfaces'] > 0 and 'NATIVE-ADMISSION-PREFIX-OK\n' in content
                            and 'GAMBIT-PROCESS-STATISTICS ' in content and '*** ERROR' not in content)
        else:
            output_valid = (report['preparedModules'] == 187 and 'MODULES 187\nIMPORT-OK\n' in content
                            and 'GAMBIT-PROCESS-STATISTICS ' in content)
        if not output_valid:
            raise RuntimeError('real preparation did not complete its original output contract')
        toc = subprocess.check_output(['xcrun', 'xctrace', 'export', '--input', str(output / 'profile.trace'), '--toc'],
                                      env=env, timeout=120)
        (output / 'toc.xml').write_bytes(toc)
        target = ET.fromstring(toc).find('./run/info/target/process')
        if target is None or target.get('return-exit-status') != '0':
            raise RuntimeError('native target exit status is not zero')
        report['targetPid'] = int(target.get('pid'))
        report['targetExitCode'] = 0
        subprocess.run(['xcrun', 'xctrace', 'export', '--input', str(output / 'profile.trace'),
                        '--xpath', '/trace-toc/run[@number="1"]/data/table[@schema="cpu-profile"]',
                        '--output', str(output / 'cpu-profile.xml')],
                       env=env, check=True, timeout=120, stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE)
        report['recordingComplete'] = True
        report['qualified'] = True
    except BaseException as error:
        report['failure'] = str(error)
        raise
    finally:
        report['wallSeconds'] = time.monotonic()-started
        report['hostLoadEnd'] = os.getloadavg()
        (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    main()
