"""Regenerate original Gambit static metadata for newly introduced diagnostic globals."""
import argparse
import hashlib
import json
from pathlib import Path
import shlex
import subprocess

from bazel_host_environment import build_environment


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--source', type=Path, required=True)
    args = parser.parse_args()
    source = args.source.resolve()
    repo = Path(__file__).resolve().parents[3]
    if not source.is_relative_to(repo / '.data'):
        parser.error('isolated project-data source required')
    lib = source / 'src/gambit/lib'
    path = source / 'source-cost-preparation.json'
    report = json.loads(path.read_text())
    if (not report.get('fullMacroContextGenerationPassed')
            or report['generatedCSha256'] != hashlib.sha256((lib / '_eval.c').read_bytes()).hexdigest()):
        raise RuntimeError('original diagnostic generation provenance changed')
    home = args.baseline.resolve() / 'build'
    env = build_environment()
    env.update(GERBIL_HOME=str(home), GERBIL_LOADPATH=str(home / 'lib'),
               GAMBOPT=f"~~bin={home / 'bin'},~~lib={home / 'lib'},~~include={home / 'include'}")
    dry = subprocess.check_output(['make', '-n', '-B', '_gambit.c'], cwd=lib, env=env, text=True)
    commands = [shlex.split(line) for line in dry.splitlines()
                if line.lstrip().startswith('../gsc-boot ') and ' -link -flat ' in line]
    if len(commands) != 1:
        raise RuntimeError('ambiguous original static metadata generation command')
    command = commands[0]
    command[0] = str(home / 'bin/gsc')
    command[1] = f"-:~~bin={home / 'bin'},~~lib={lib},~~include={home / 'include'}"
    with (source / 'generate-static-metadata.log').open('w') as log:
        subprocess.run(command, cwd=lib, env=env, stdout=log, stderr=subprocess.STDOUT,
                       timeout=300, check=True)
    report['staticMetadataGenerationCommand'] = command
    report['generatedLinkCSha256'] = hashlib.sha256((lib / '_gambit.c').read_bytes()).hexdigest()
    path.write_text(json.dumps(report, indent=2) + '\n')
    print('SOURCE-COST-METADATA-PREPARED original flat/preload policy', flush=True)


if __name__ == '__main__':
    main()
