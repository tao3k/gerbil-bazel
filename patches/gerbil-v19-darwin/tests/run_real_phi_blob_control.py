"""Real generated phase-body serialization, not ordinary-module admission."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time

from bazel_host_environment import build_environment
from progressive_performance_gate import force_stop


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--inspect-only', action='store_true')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    out = args.output.resolve()
    if not out.is_relative_to(root / '.data') or out.exists():
        parser.error('fresh persistent data directory required')
    binary = root / '.data/d1510-reader-whitespace-native-v2/gerbil'
    home = root / '.data/d1510-mcp-test-source-home-v2/build'
    project = root / '.data/d1510-reader-whitespace-progressive-v1/0-candidate/project'
    driver = root / '.data/d1510-shell-substitution/bin'
    source = project / '.gerbil/lib/gerbil-mcp/util/strings~1.scm'
    source_sha = hashlib.sha256(source.read_bytes()).hexdigest()
    expected = '1f83878a01744817ceb6e74e5d07138948930a41386e568d156210ce9108bb21'
    if hashlib.sha256(binary.read_bytes()).hexdigest() != expected:
        raise ValueError('frozen host changed')
    out.mkdir()
    gxi = out / 'gxi'
    gxi.symlink_to(binary)
    env = build_environment()
    for key in tuple(env):
        if key.startswith('GAMBIT_DARWIN_') or key == 'GERBIL_BUILD_PREFIX':
            env.pop(key)
    env.update(GERBIL_HOME=str(home), GERBIL_PATH=str(project / '.gerbil'),
               GERBIL_LOADPATH=f'{project / ".gerbil/lib"}:{home / "lib"}:{project}',
               GAMBIT_EMBEDDED_NATIVE='0', GERBIL_GSC=str(driver / 'gsc'),
               GERBIL_GCC=env['GERBIL_GNU_GCC'],
               GAMBOPT=f'~~bin={driver},~~lib={home / "lib"},~~include={home / "include"}',
               REAL_PHI_SOURCE=str(source), REAL_PHI_BLOB=str(out / 'phase.bin'),
               REAL_PHI_MODULE_DIR=str(out))
    fixture = Path(__file__).with_name('real_phi_blob_control.scm')
    report = dict(scope='real-generated-phase-body-with-ordinary-load-wrapper-controls',
                  qualified=False, productionAdmitted=False, performanceQualified=False,
                  binarySha256=expected, sourceSha256=source_sha, runs=[])
    try:
        modes = ([('inspect', 1)] if args.inspect_only else
                 [('produce', 3), ('native', 5), ('source', 5), ('restore', 6),
                  ('module', 7), ('native', 5), ('module', 7), ('native', 5)])
        for mode, count in modes:
            index = len(report['runs'])
            path = out / f'{index}-{mode}.log'
            started = time.monotonic()
            with path.open('wb') as log:
                child = subprocess.Popen([str(gxi), '-e', '(load ' + json.dumps(str(fixture)) + ')'],
                    cwd=project, env=dict(env, REAL_PHI_MODE=mode), stdout=log,
                    stderr=subprocess.STDOUT, start_new_session=True)
                try:
                    code = child.wait(timeout=20)
                finally:
                    if child.poll() is None:
                        force_stop(child)
            text = path.read_text(errors='replace')
            cases = [line for line in text.splitlines() if line.startswith('CASE-OK ')]
            passed = (code == 0 and len(cases) == len(set(cases)) == count and
                      text.splitlines()[-1:] == ['OK'] and '*** ERROR' not in text)
            report['runs'].append(dict(mode=mode, passed=passed, exitCode=code,
                                       wallSeconds=time.monotonic() - started, cases=cases))
            timing = [line.split('\t') for line in text.splitlines()
                      if line.startswith('PHASE-INIT-COST\t')]
            if mode not in ('produce', 'inspect'):
                if len(timing) != 1 or len(timing[0]) != 4 or timing[0][1] != mode:
                    report['runs'][-1]['passed'] = False
                    passed = False
                else:
                    report['runs'][-1].update(initializationSeconds=float(timing[0][2]),
                                              initializationAllocatedBytes=float(timing[0][3]))
            if not passed:
                break
        report['sourceUnchanged'] = hashlib.sha256(source.read_bytes()).hexdigest() == source_sha
        report['qualified'] = (not args.inspect_only and len(report['runs']) == 8 and
                               report['sourceUnchanged'] and
                               all(row['passed'] for row in report['runs']))
    except Exception as error:
        report['failure'] = repr(error)
    (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))
    return 0 if report['qualified'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
