"""Consumer-only C runtime deployment using the unchanged frozen CLI and gates."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import run_d1510_progressive as progressive
from verify_reader_batch_50_baseline import main as verify


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    output = args.output.resolve()
    if not output.is_relative_to(root / '.data') or output.exists():
        parser.error('fresh persistent output required')
    verify()
    prefix = root / '.data/d1510-fork-fd-consumer-prefix-v1'
    archive = prefix / 'lib/libgambit.a'
    construction = json.loads((prefix / 'report.json').read_text())
    controls = json.loads((root / '.data/d1510-fork-fd-consumer-controls-v2/report.json').read_text())
    if (not construction['constructionQualified'] or not controls['consumerControlsQualified'] or
            sha(archive) != construction['archiveSha256'] or
            construction['archiveSha256'] != controls['archiveSha256']):
        raise ValueError('private C runtime deployment not qualified')
    binary = root / '.data/d1510-reader-batch-native-v1/gerbil'
    home = root / '.data/d1391-runtime-object-source/build'
    original_hash = sha(home / 'lib/libgambit.a')
    before = dict(hostBinarySha256=sha(binary), consumerArchiveSha256=sha(archive),
                  originalArchiveSha256=original_hash, driverHarnessSha256=sha(Path(progressive.__file__)),
                  wrapperSha256=sha(Path(__file__)))
    instrument = progressive.instrument_cold_controller

    def consumer_instrument(source, ceiling):
        source = instrument(source, ceiling)
        anchor = '    return env\n'
        if source.count(anchor) != 1:
            raise ValueError('retained cold environment boundary drift')
        return source.replace(anchor, "    env['GERBIL_BUILD_PREFIX'] = str(ROOT / " +
                              repr(str(prefix.relative_to(root))) + ')\n' + anchor, 1)

    old_argv = sys.argv
    progressive.instrument_cold_controller = consumer_instrument
    report = dict(scope='frozen-host-private-consumer-c-runtime', inputs=before,
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
        report['consumerDeploymentQualified'] = bool(deployments) and all(
            entry['forkProbeLinked'] for entry in deployments)
        report['pipeline'] = json.loads((output / 'progressive-admission.json').read_text())
        unchanged = (before['hostBinarySha256'] == sha(binary) and
                     before['consumerArchiveSha256'] == sha(archive) and
                     original_hash == sha(home / 'lib/libgambit.a'))
        report['frozenInputsUnchanged'] = unchanged
        report['qualified'] = status == 0 and unchanged and report['consumerDeploymentQualified']
        return 0 if report['qualified'] else 1
    finally:
        progressive.instrument_cold_controller = instrument
        sys.argv = old_argv
        if output.exists():
            (output / 'consumer-deployment.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    raise SystemExit(main())
