"""Compose already-built Gambit execution and image candidates, not a production patch."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

from macho_image_dependencies import validate_packed_image_inventory
from run_mcp_native_cpu_profile import candidate_provenance_valid


SCOPE = 'current-staging-gambit-runtime-and-packed-images-composition'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_composed_runtime(home, receipt, original_home):
    if (receipt.get('scope') != SCOPE or receipt.get('qualified') is not True
            or receipt.get('gscUnchanged') is not True or receipt.get('runtimeAbiChanged') is not False
            or receipt.get('consumerFlagsChanged') is not False
            or receipt.get('originalGambitMacroInputsUsed') is not True):
        raise ValueError('qualified unchanged-ABI composition receipt required')
    runtime = receipt['runtimeBuildReceipt']
    if not candidate_provenance_valid(runtime, digest(home/'bin/gxi'), digest(original_home/'bin/gsc')):
        raise ValueError('composed runtime/compiler provenance changed')
    if (digest(home/'bin/gsc') != digest(original_home/'bin/gsc')
            or digest(home/'include/gambit.h') != digest(original_home/'include/gambit.h')
            or digest(home/'include/gambit.h') != receipt['headerSha256']):
        raise ValueError('composition changed compiler or public runtime header')
    validate_packed_image_inventory(home, receipt)
    return True


def main():
    parser = argparse.ArgumentParser()
    for name in ('baseline', 'runtime-source', 'runtime-receipt', 'image-source', 'image-receipt', 'output'):
        parser.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    paths = {name: getattr(args, name).resolve() for name in
             ('baseline', 'runtime_source', 'runtime_receipt', 'image_source', 'image_receipt', 'output')}
    if not all(path.is_relative_to(root/'.data') for path in paths.values()):
        parser.error('isolated project-data composition required')
    original, runtime_home, image_home = (paths[key]/'build' for key in ('baseline', 'runtime_source', 'image_source'))
    runtime = json.loads(paths['runtime_receipt'].read_text())
    images = json.loads(paths['image_receipt'].read_text())
    if not candidate_provenance_valid(runtime, digest(runtime_home/'bin/gxi'), digest(original/'bin/gsc')):
        parser.error('completed uninstrumented unchanged-ABI runtime build required')
    if (images.get('qualified') is not True or images.get('originalGambitMacroInputsUsed') is not True
            or images.get('officialToolsIncluded') is not True
            or images.get('scope') != 'current-staging-native-preload-image-packing-prototype'
            or (root/images['candidate']).resolve() != paths['image_source']
            or digest(image_home/'bin/gxi') != digest(original/'bin/gxi')
            or digest(image_home/'bin/gsc') != digest(original/'bin/gsc')
            or digest(runtime_home/'bin/gsc') != digest(original/'bin/gsc')
            or any(digest(home/'include/gambit.h') != images['headerSha256']
                   for home in (image_home, runtime_home, original))):
        parser.error('current original-compiler/header image inputs required')
    validate_packed_image_inventory(image_home, images)
    for row in images['units']:
        if (digest(original/row['path']) != row['originalSha256']
                or digest((original/row['path']).with_suffix('.scm')) != row['sourceSha256']
                or digest((image_home/row['path']).with_suffix('.scm')) != row['sourceSha256']):
            parser.error('original image/source inputs changed')
    output = paths['output']
    output.mkdir(parents=True, exist_ok=False)
    candidate = output/'source'
    subprocess.run(['/bin/cp', '-cR', str(paths['image_source']), str(candidate)], check=True, timeout=60)
    home = candidate/'build'
    subprocess.run(['/bin/cp', '-c', str(runtime_home/'bin/gerbil'), str(home/'bin/gerbil')], check=True, timeout=30)
    report = dict(images)
    report.update(qualified=False, performanceQualified=False, diagnosticOnly=False, scope=SCOPE,
                  originalHome=str(original.relative_to(root)), runtimeSource=str(paths['runtime_source'].relative_to(root)),
                  candidate=str(candidate.relative_to(root)), binaryHashesUnchanged=False,
                  gscUnchanged=True, originalRuntimeSha256=digest(original/'bin/gxi'),
                  runtimeBuildReceipt=runtime,
                  runtimeBuildReceiptSha256=digest(paths['runtime_receipt']),
                  imageBuildReceiptSha256=digest(paths['image_receipt']),
                  binaryHashes=dict(gxi=digest(home/'bin/gxi'), gsc=digest(home/'bin/gsc')),
                  nativeSuiteQualified=False, runtimeAbiChanged=False, consumerFlagsChanged=False)
    report['qualified'] = True
    validate_composed_runtime(home, report, original)
    (output/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    print(f'COMPOSITION-BUILT images={len(report["images"])} runtime={report["binaryHashes"]["gxi"]}', flush=True)


if __name__ == '__main__':
    main()
