"""Deploy the qualified Darwin C object only at final executable linkage."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys

from bazel_host_environment import build_environment
import run_d1510_progressive as progressive
from verify_reader_whitespace_47_baseline import main as verify


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def render_wrapper(compiler, obj, log):
    return f'''#!/bin/sh
compile=no
runtime=no
for argument do
  case "$argument" in
    -c|-E|-S) compile=yes ;;
    -lgambit) runtime=yes ;;
  esac
done
if test "$compile" = no && test "$runtime" = yes; then
  printf '%s\\n' LINK "$@" >> {shlex.quote(str(log))}
  exec {shlex.quote(str(compiler))} {shlex.quote(str(obj))} "$@"
fi
exec {shlex.quote(str(compiler))} "$@"
'''


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--tools', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    output, tools = args.output.resolve(), args.tools.resolve()
    if (os.uname().sysname != 'Darwin' or any(
            not p.is_relative_to(root / '.data') or p.exists() for p in (output, tools))):
        parser.error('fresh isolated Darwin outputs required')
    verify()
    prefix = root / '.data/d1510-fork-fd-consumer-prefix-v1'
    construction = json.loads((prefix / 'report.json').read_text())
    controls = json.loads((root / '.data/d1510-fork-fd-consumer-controls-v2/report.json').read_text())
    obj = prefix / 'os_io.o'
    if (not construction['constructionQualified'] or not controls['consumerControlsQualified'] or
            sha(obj) != construction['memberHashes']['os_io.o'] or
            sha(prefix / 'lib/libgambit.a') != controls['archiveSha256']):
        raise ValueError('qualified consumer C object identity changed')
    env = build_environment()
    compiler = Path(env['GERBIL_GNU_GCC']).resolve(strict=True)
    version = subprocess.check_output([str(compiler), '--version'], text=True)
    if 'clang' in version.lower() or not ('gcc' in version.lower() or 'GNU' in version):
        raise ValueError('explicit GNU GCC required')
    tools.mkdir()
    wrapper = tools / 'gcc-final-runtime'
    links = tools / 'links.log'
    wrapper.write_text(render_wrapper(compiler, obj, links))
    wrapper.chmod(0o755)
    binary = root / '.data/d1510-reader-whitespace-native-v2/gerbil'
    home = root / '.data/d1391-runtime-object-source/build'
    before = dict(hostBinarySha256=sha(binary), originalArchiveSha256=sha(home / 'lib/libgambit.a'),
                  consumerObjectSha256=sha(obj), compilerSha256=sha(compiler),
                  wrapperSha256=sha(wrapper))
    instrument = progressive.instrument_cold_controller

    def link_only_instrument(source, ceiling):
        source = instrument(source, ceiling)
        anchor = '    return env\n'
        if source.count(anchor) != 1:
            raise ValueError('retained environment boundary changed')
        return source.replace(anchor, '    env["GERBIL_GCC"] = ' + repr(str(wrapper)) + '\n' + anchor)

    old_argv = sys.argv
    progressive.instrument_cold_controller = link_only_instrument
    report = dict(scope='frozen-47s-host-final-GNU-executable-C-object-only',
                  constructionInputs=before, prefixChanged=False, compilerFlagsChanged=False,
                  consumerDeploymentQualified=False, qualified=False)
    try:
        sys.argv = [progressive.__file__, '--binary', str(binary), '--output', str(output),
                    '--test-home', str(root / '.data/d1510-mcp-test-source-home-v2/build'),
                    '--cold-runs', '3']
        status = progressive.main()
        cold = json.loads((output / 'report.json').read_text())
        deployments = []
        for index, row in enumerate(cold.get('runs', [])):
            if row['passed']:
                executable = output / f'{index}-candidate/project/.gerbil/bin/gerbil-mcp'
                symbols = subprocess.check_output(['/usr/bin/nm', str(executable)], timeout=10).decode()
                deployments.append(dict(round=index, executableSha256=sha(executable),
                                        forkProbeLinked=' U _proc_pidinfo' in symbols))
        report['deployments'] = deployments
        report['consumerDeploymentQualified'] = len(deployments) == 3 and all(
            row['forkProbeLinked'] for row in deployments)
        report['pipeline'] = json.loads((output / 'progressive-admission.json').read_text())
        report['frozenInputsUnchanged'] = (sha(binary) == before['hostBinarySha256'] and
                                          sha(home / 'lib/libgambit.a') == before['originalArchiveSha256'] and
                                          sha(obj) == before['consumerObjectSha256'])
        report['qualified'] = (status == 0 and report['consumerDeploymentQualified'] and
                               report['frozenInputsUnchanged'])
        return 0 if report['qualified'] else 1
    finally:
        progressive.instrument_cold_controller = instrument
        sys.argv = old_argv
        if output.exists():
            (output / 'consumer-link-deployment.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    raise SystemExit(main())
