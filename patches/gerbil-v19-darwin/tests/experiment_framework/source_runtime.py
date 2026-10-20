"""Owned source-aware runtime fixture; never modify the selected runtime."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def prepare(runtime, source, output, copy_runtime):
    if output.exists() or output.is_symlink():
        raise ValueError('fresh output required')
    if (runtime == output or runtime.is_relative_to(output)
            or output.is_relative_to(runtime) or source.is_relative_to(output)
            or output.is_relative_to(source)):
        raise ValueError('runtime/source/output must not overlap')
    if (runtime / 'src').exists() or (runtime / 'src').is_symlink():
        raise ValueError('runtime already has source; do not replace it')
    files = sorted(p for tree in ('gerbil', 'std', 'lang', 'tools')
                   for p in (source / tree).rglob('*.ss'))
    if not files:
        raise ValueError('source tree required')
    identity = {}
    for name in ('include/gambit.h', 'lib/libgambit.a', 'lib/libgambitgsc.a'):
        path = runtime / name
        if path.is_symlink() or not path.is_file():
            raise ValueError('regular runtime prerequisite required')
        identity[name] = sha(path)
    records = {}
    for path in files:
        if path.is_symlink() or not path.is_file():
            raise ValueError('regular source required')
        records[str(Path('src') / path.relative_to(source))] = sha(path)
    copy_runtime(runtime, output)
    for path in files:
        destination = output / 'src' / path.relative_to(source)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, destination)
        if sha(destination) != records[str(destination.relative_to(output))]:
            raise ValueError('source changed while copying')
    if any(sha(output / name) != digest for name, digest in identity.items()):
        raise ValueError('runtime changed while copying')
    return dict(schema='owned-source-runtime-v1', sourceFiles=records,
                runtimeFiles=identity, originalRuntimeUnmodified=True)


def verify(output, record):
    for group in ('sourceFiles', 'runtimeFiles'):
        for name, digest in record[group].items():
            relative = Path(name)
            if relative.is_absolute() or '..' in relative.parts:
                raise ValueError('invalid fixture identity path')
            path = output / relative
            if (path.is_symlink() or not path.is_file()
                    or any(parent.is_symlink() for parent in path.parents
                           if parent.is_relative_to(output)) or sha(path) != digest):
                raise ValueError('source/runtime fixture drift: ' + name)
    return len(record['sourceFiles'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime', type=Path, required=True)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--reference-images', action='store_true',
                        help='content-checked read-only original dynamic images; static files remain owned')
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[4]
    runtime, source, output = [p.absolute() for p in (args.runtime, args.source, args.output)]
    for path in (runtime, source, output):
        if not path.resolve().is_relative_to(root / '.data'):
            parser.error('owned .data paths required')
    if args.verify:
        record = json.loads((output / 'source-fixture.json').read_text())
        count = verify(output, record)
        if record.get('readOnlyDynamicImages'):
            from ascent_profile import verify_images
            verify_images(output, output / 'source-fixture.json')
        print(f'SOURCE-RUNTIME-VERIFIED sources={count} identity-only')
        return
    if sys.platform != 'darwin':
        parser.error('APFS clone preparation requires Darwin')
    def clone(original, destination):
        subprocess.run(['/bin/cp', '-cR', str(original), str(destination)], check=True)
    record = prepare(runtime, source, output, clone)
    if args.reference_images:
        from ascent_profile import reference_images
        record['readOnlyDynamicImages'] = reference_images(runtime, output, ('.o1', '.o2'))
    (output / 'source-fixture.json').write_text(json.dumps(record, indent=2) + '\n')
    print(f'SOURCE-RUNTIME-READY sources={len(record["sourceFiles"])} original-unmodified')


if __name__ == '__main__':
    main()
