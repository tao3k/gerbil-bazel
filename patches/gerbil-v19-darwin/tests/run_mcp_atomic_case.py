"""Execute one original std/test case; never claim complete-suite admission."""
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import selectors
import subprocess
import time

from bazel_host_environment import build_environment
from mcp_case_inventory import case_names
from progressive_performance_gate import ProgressiveGate, Limits, force_stop
from selected_gerbil_toolchain import validate_tools
from run_complete_mcp_wave import final_test_ok, TEST_CEILING_SECONDS


def atomic_admission(text, exit_code, wanted, source_unchanged):
    actual = [line[8:] for line in text.splitlines() if line.startswith('CASE-OK ')]
    return (exit_code == 0 and final_test_ok(text) and
            Counter(actual) == Counter([wanted]) and source_unchanged and
            'CASE-FAIL' not in text and '*** ERROR' not in text)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--file', choices=('chunk-07-test.ss', 'chunk-12-test.ss'), required=True)
    parser.add_argument('--case', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    project = root / '.data/d1510-reader-whitespace-progressive-v1/0-candidate/project'
    binary = root / '.data/d1510-reader-whitespace-native-v2/gerbil'
    home = root / '.data/d1510-mcp-test-source-home-v2/build'
    driver = root / '.data/d1510-shell-substitution/bin'
    out = args.output.resolve()
    file = project / 'test' / args.file
    if not out.is_relative_to(root / '.data') or out.exists() or args.case not in case_names(file):
        parser.error('fresh .data output and exact original case name required')
    expected = '1f83878a01744817ceb6e74e5d07138948930a41386e568d156210ce9108bb21'
    if hashlib.sha256(binary.read_bytes()).hexdigest() != expected:
        raise ValueError('frozen host changed')
    before = hashlib.sha256(file.read_bytes()).hexdigest()
    out.mkdir()
    entry, tmp = out / 'selected-bin', out / 'tmp'
    entry.mkdir()
    tmp.mkdir()
    env = build_environment()
    for key in tuple(env):
        if key.startswith('GAMBIT_DARWIN_') or key == 'GERBIL_BUILD_PREFIX':
            env.pop(key)
    cores = int(subprocess.check_output(['sysctl', '-n', 'hw.physicalcpu'], text=True))
    env.update(GERBIL_HOME=str(home), GERBIL_PATH=str(project / '.gerbil'),
               GERBIL_LOADPATH=f'{project / ".gerbil/lib"}:{home / "lib"}:{project}',
               PATH=f'{entry}:{driver}:{home / "bin"}:{env["PATH"]}', TMPDIR=str(tmp),
               GERBIL_GSC=str(driver / 'gsc'), GERBIL_GCC=env['GERBIL_GNU_GCC'],
               GERBIL_BUILD_CORES=str(cores),
               GAMBOPT=f'~~bin={driver},~~lib={home / "lib"},~~include={home / "include"}',
               GAMBIT_EMBEDDED_NATIVE='0', GERBIL_MCP_MODE='full',
               GERBIL_MCP_BIN=str(project / '.gerbil/bin/gerbil-mcp'),
               MCP_ATOMIC_CASE=args.case, MCP_ATOMIC_FILE=str(file))
    for name in ('gerbil', 'gxi', 'gxc', 'gxpkg'):
        (entry / name).symlink_to(binary)
        env['GERBIL_MCP_' + name.upper() + '_PATH'] = str(entry / name)
    validate_tools(env, binary, expected)
    started = time.monotonic()
    gate = ProgressiveGate(Limits('atomic-original-case', complete=TEST_CEILING_SECONDS,
                                 first=5, silence=None), started)
    report = dict(scope='one-original-std-test-case', fullSuiteQualified=False, atomicPassed=False,
                  binarySha256=expected, testFile='test/' + args.file, case=args.case,
                  physicalBuildCores=cores)
    source = Path(__file__).with_name('mcp_atomic_case.ss')
    process = subprocess.Popen([str(entry / 'gxi'), str(source)], cwd=project, env=env,
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT, start_new_session=True)
    selector = selectors.DefaultSelector()
    selector.register(process.stdout, selectors.EVENT_READ)
    try:
        with (out / 'atomic.log').open('wb') as log:
            while selector.get_map() or process.poll() is None:
                gate.check(time.monotonic())
                for key, _ in selector.select(.05):
                    chunk = os.read(key.fileobj.fileno(), 65536)
                    if not chunk:
                        selector.unregister(key.fileobj)
                        continue
                    observed = time.monotonic()
                    gate.output(observed)
                    gate.first(observed)
                    log.write(chunk)
                    log.flush()
        report['exitCode'] = process.wait(timeout=1)
        text = (out / 'atomic.log').read_text(errors='replace')
        report['caseTimings'] = [json.loads(line) for line in text.splitlines() if line.startswith('{')]
        report['sourceUnchanged'] = hashlib.sha256(file.read_bytes()).hexdigest() == before
        report['atomicPassed'] = (atomic_admission(text, report['exitCode'], args.case,
                                                   report['sourceUnchanged']) and
                                 len(report['caseTimings']) == 1 and
                                 report['caseTimings'][0].get('atomicCase') == args.case)
    except Exception as error:
        report['failure'] = repr(error)
    finally:
        selector.close()
        if process.poll() is None:
            report['cleanup'] = force_stop(process)
        report.update(wallSeconds=time.monotonic() - started, firstOutputSeconds=gate.first_event)
        (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))
    return 0 if report['atomicPassed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
