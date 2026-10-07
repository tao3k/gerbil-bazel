"""Verify the frozen original line; never admit historical timing as current."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath

LOCK = Path(__file__).resolve().parents[1] / 'receipts/d1510-retained-56-baseline.json'


def relative_file(root, name):
    path = PurePosixPath(name)
    if path.is_absolute() or '..' in path.parts or not path.parts or path.parts[0] != '.data':
        raise ValueError('Expected project-relative .data input')
    result = root / name
    if not result.resolve().is_relative_to((root / '.data').resolve()):
        raise ValueError('Input escapes project .data')
    return result


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(root, lock):
    if (lock['schemaVersion'] != 1 or lock['fullBuildCeilingSeconds'] != 55
            or lock['currentPerformanceReproduced'] is not False
            or lock['fallback']['performanceGatePassed'] is not False):
        raise ValueError('Historical fallback cannot change the admission gate')
    for name, expected in lock['files'].items():
        if digest(relative_file(root, name)) != expected:
            raise ValueError('Frozen input changed: ' + name)
    binary = relative_file(root, lock['baselineBinary'])
    if (binary.parent / 'gxi').resolve() != binary.resolve():
        raise ValueError('Original gxi alias changed')
    receipt = json.loads(relative_file(root, lock['fallback']['receipt']).read_text())
    if len(receipt['runs']) != 1:
        raise ValueError('Unexpected fallback run count')
    row = receipt['runs'][0]
    for field in ('firstCompileSeconds', 'buildWallSeconds', 'cleanExitCode',
                  'buildExitCode', 'nativeImagesAfterClean'):
        if row[field] != lock['fallback'][field]:
            raise ValueError('Fallback evidence changed: ' + field)
    if row['binarySha256'] != lock['files'][lock['baselineBinary']] or not row['sourceUnchanged']:
        raise ValueError('Fallback is not the frozen original')
    configuration = json.loads(relative_file(root, lock['fallback']['configuration']).read_text())
    compiler = Path(configuration['environment']['CC']).resolve()
    compiler_ref = lock['compilerDriverReference']
    if (digest(compiler) != compiler_ref['sha256']
            or configuration['files'].get(str(compiler)) != compiler_ref['sha256']
            or configuration['gccVersion'].splitlines()[0] != compiler_ref['versionLine']
            or Path(configuration['environment']['SDKROOT']).name != compiler_ref['sdkName']):
        raise ValueError('Frozen GNU compiler driver changed')
    home = relative_file(root, lock['runtimeHome'])
    reference = lock['runtimeHomeReference']
    inventory = json.loads(relative_file(root, reference['receipt']).read_text())
    if not inventory['qualified'] or len(inventory['units']) != reference['moduleCount']:
        raise ValueError('Runtime home reference is incomplete')
    for unit in inventory['units']:
        base = home / 'lib' / unit['module']
        version = 1
        while Path(str(base) + '.o' + str(version)).is_file():
            version += 1
        selected = Path(str(base) + '.o' + str(version - 1))
        if (version == 1 or selected != home / unit['path']
                or digest(selected) != unit['originalSha256']
                or digest(Path(str(base) + '.scm')) != unit['sourceSha256']):
            raise ValueError('Runtime module changed: ' + unit['module'])
    return dict(verified=True, line=lock['line'], lockedFiles=len(lock['files']),
                compilerDriverVerified=True,
                runtimeModules=reference['moduleCount'],
                historicalFallbackSeconds=row['buildWallSeconds'],
                historicalFirstCompileSeconds=row['firstCompileSeconds'],
                currentPerformanceReproduced=False, performanceQualified=False,
                fullBuildCeilingSeconds=55)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[3])
    args = parser.parse_args()
    print(json.dumps(verify(args.root.resolve(), json.loads(LOCK.read_text())), indent=2))


if __name__ == '__main__':
    main()
