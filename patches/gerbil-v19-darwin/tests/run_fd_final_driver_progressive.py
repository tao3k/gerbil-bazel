"""Use the real GNU compiler and a guarded final-link-only driver hook."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import run_d1510_progressive as progressive


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--binary', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    binary, output = args.binary.resolve(), args.output.resolve()
    if any(not p.is_relative_to(root / '.data') for p in (binary, output)) or output.exists():
        parser.error('isolated binary and fresh output required')
    construction = json.loads((binary.parent / 'report.json').read_text())
    component = root / '.data/d1510-fork-fd-consumer-prefix-v1'
    controls = json.loads((root / '.data/d1510-fork-fd-consumer-controls-v2/report.json').read_text())
    obj = component / 'os_io.o'
    component_report = json.loads((component / 'report.json').read_text())
    if (not construction['qualified'] or not construction['globalsUnchanged'] or
            sha(binary) != construction['binarySha256'] or not controls['consumerControlsQualified'] or
            sha(obj) != component_report['memberHashes']['os_io.o']):
        raise ValueError('construction or qualified C-object identity mismatch')
    instrument = progressive.instrument_cold_controller
    old_argv = sys.argv

    def hook(source, ceiling):
        source = instrument(source, ceiling)
        anchor = '    return env\n'
        if source.count(anchor) != 1:
            raise ValueError('exact retained environment boundary required')
        return source.replace(anchor, '    env["GAMBIT_DARWIN_RUNTIME_OBJECT"] = ' +
                              repr(str(obj)) + '\n' + anchor)

    progressive.instrument_cold_controller = hook
    report = dict(scope='Darwin-final-driver-hook-C-object-deployment', qualified=False,
                  hostBinarySha256=sha(binary), objectSha256=sha(obj),
                  compilerWrapperUsed=False, prefixChanged=False, deployments=[])
    try:
        sys.argv = [progressive.__file__, '--binary', str(binary), '--output', str(output),
                    '--test-home', str(root / '.data/d1510-mcp-test-source-home-v2/build'),
                    '--cold-runs', '3']
        status = progressive.main()
        cold = json.loads((output / 'report.json').read_text())
        for index, row in enumerate(cold.get('runs', [])):
            if row.get('passed'):
                executable = output / f'{index}-candidate/project/.gerbil/bin/gerbil-mcp'
                symbols = subprocess.check_output(['/usr/bin/nm', str(executable)], timeout=10).decode()
                report['deployments'].append(dict(round=index, executableSha256=sha(executable),
                                                  forkProbeLinked=' U _proc_pidinfo' in symbols))
        report['pipeline'] = json.loads((output / 'progressive-admission.json').read_text())
        report['consumerDeploymentQualified'] = len(report['deployments']) == 3 and all(
            row['forkProbeLinked'] for row in report['deployments'])
        report['qualified'] = status == 0 and report['consumerDeploymentQualified']
        return 0 if report['qualified'] else 1
    finally:
        progressive.instrument_cold_controller = instrument
        sys.argv = old_argv
        if output.exists():
            (output / 'final-driver-deployment.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    raise SystemExit(main())
