"""Prepare read-only dynamic-image references; keep static outputs isolated."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def reference_images(original, isolated, suffixes=('.o1',)):
    original, isolated = original.resolve(), isolated.resolve()
    if original == isolated or original.is_relative_to(isolated):
        raise ValueError('original and isolated roots must be disjoint')
    planned = []
    if not suffixes or any(suffix not in ('.o1', '.o2') for suffix in suffixes):
        raise ValueError('unsupported dynamic image suffix')
    for destination in sorted(path for suffix in suffixes for path in isolated.rglob('*' + suffix)):
        if destination.is_symlink():
            raise ValueError('existing dynamic-image symlink')
        relative = destination.relative_to(isolated)
        source = original / relative
        if source.is_symlink() or not source.is_file():
            raise ValueError('original image must be a regular file')
        sha = digest(source)
        if sha != digest(destination):
            raise ValueError('dynamic-image identity drift')
        planned.append((source, destination, str(relative), sha))
    if not planned:
        raise ValueError('no dynamic images found')
    for source, destination, _, _ in planned:
        destination.unlink()
        destination.symlink_to(source)
    return [{'path': relative, 'sha256': sha} for _, _, relative, sha in planned]


def protect_driver(path):
    text = path.read_text()
    anchor = 'case "$1" in\n\n  "obj")'
    if text.count(anchor) != 1:
        raise ValueError('driver dispatch drift')
    guard = '''# Qualification only: never compile through a read-only image reference.
case "$1" in
  obj) isolation_output=${BUILD_OBJ_OUTPUT_FILENAME_PARAM-} ;;
  dyn) isolation_output=${BUILD_DYN_OUTPUT_FILENAME_PARAM-} ;;
  exe) isolation_output=${BUILD_EXE_OUTPUT_FILENAME_PARAM-} ;;
  lib) isolation_output=${BUILD_LIB_OUTPUT_FILENAME_PARAM-} ;;
  *) isolation_output= ;;
esac
if test -n "$isolation_output" && test -L "$isolation_output"; then
  printf 'ISOLATION-OUTPUT-SYMLINK-DENY\\n' >&2
  exit 2
fi

'''
    path.write_text(text.replace(anchor, guard + anchor, 1))


def verify_images(isolated, receipt):
    document = json.loads(receipt.read_text())
    records = document['readOnlyDynamicImages']
    for record in records:
        relative = Path(record['path'])
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError('invalid image path')
        destination = isolated / relative
        if not destination.is_symlink():
            raise ValueError('read-only dynamic image is not a reference: ' + str(relative))
        actual = digest(destination)
        if actual != record['sha256']:
            raise ValueError(f'read-only dynamic image drift: {relative}; expected={record["sha256"]}; actual={actual}')
    for overlay in document.get('ownedModuleOverlays', []):
        for record in overlay['files']:
            relative = Path(record['path'])
            if relative.is_absolute() or '..' in relative.parts:
                raise ValueError('invalid overlay path')
            path = isolated / relative
            if path.is_symlink() or digest(path) != record['sha256']:
                raise ValueError('owned module overlay drift: ' + str(relative))
    return len(records)


def install_module_overlay(isolated, library, module, receipt):
    parts = module.split('/')
    if not all(part and all(c.isalnum() or c in '_-' for c in part) for part in parts):
        raise ValueError('invalid overlay module')
    if isolated.resolve() == library.resolve():
        raise ValueError('overlay and isolated roots must differ')
    verify_images(isolated, receipt)
    document = json.loads(receipt.read_text())
    if any(item['module'] == module for item in document.get('ownedModuleOverlays', [])):
        raise ValueError('module already overlaid')
    stem = Path(*parts)
    source_directory = library / stem.parent
    candidates = sorted(path for path in source_directory.iterdir()
                        if (path.name.startswith(stem.name + '.') or path.name.startswith(stem.name + '~'))
                        and not (path.name.endswith('.dSYM') and path.is_dir() and not path.is_symlink()))
    static = Path('static') / ('__'.join(parts) + '.scm')
    candidates.append(library / static)
    if not (library / stem.with_suffix('.ssi')).is_file():
        raise ValueError('compiled overlay interface required')
    planned = []
    for source in candidates:
        if source.is_symlink() or not source.is_file():
            raise ValueError('regular overlay files required')
        relative = Path('lib') / source.relative_to(library)
        destination = isolated / relative
        if any(parent.is_symlink() for parent in destination.parents if parent != isolated.parent):
            raise ValueError('overlay destination directory symlink')
        if destination.is_symlink() and not any(record['path'] == str(relative)
                                                for record in document['readOnlyDynamicImages']):
            raise ValueError('unrecorded overlay destination symlink')
        planned.append((source, destination, str(relative), digest(source)))
    if not any(source.suffix == '.o1' for source, _, _, _ in planned):
        raise ValueError('compiled overlay image required')
    stale = [isolated / 'lib/static' / ('__'.join(parts) + extension) for extension in ('.c', '.o')]
    if any(path.is_symlink() for path in stale):
        raise ValueError('stale static artifact symlink')
    for source, destination, _, sha in planned:
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.is_symlink():
            destination.unlink()
        shutil.copy2(source, destination)
        if digest(source) != sha or digest(destination) != sha:
            raise ValueError('overlay changed during copy')
    for path in stale:
        if path.exists():
            path.unlink()
    replaced = {relative for _, _, relative, _ in planned}
    document['readOnlyDynamicImages'] = [record for record in document['readOnlyDynamicImages']
                                         if record['path'] not in replaced]
    document.setdefault('ownedModuleOverlays', []).append(dict(module=module, files=[
        dict(path=relative, sha256=sha) for _, _, relative, sha in planned]))
    receipt.write_text(json.dumps(document, indent=2) + '\n')
    verify_images(isolated, receipt)
    return len(planned)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--original', type=Path)
    parser.add_argument('--isolated', type=Path, required=True)
    parser.add_argument('--receipt', type=Path, required=True)
    parser.add_argument('--driver', type=Path)
    parser.add_argument('--verify', action='store_true')
    parser.add_argument('--overlay-library', type=Path)
    parser.add_argument('--module')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[4]
    for path in (args.isolated, args.receipt, args.driver):
        if path and not path.resolve().is_relative_to(root / '.data'):
            raise ValueError('all writes must be inside project .data')
    if args.verify:
        print(f'READONLY-DYNAMIC-IMAGES-VERIFIED {verify_images(args.isolated, args.receipt)}')
        return
    if args.overlay_library:
        if not args.overlay_library.resolve().is_relative_to(root / '.data') or not args.module:
            raise ValueError('owned overlay and module required')
        count = install_module_overlay(args.isolated, args.overlay_library, args.module, args.receipt)
        print(f'OWNED-MODULE-OVERLAY-VERIFIED {args.module} files={count}')
        return
    if not args.original:
        raise ValueError('original image root required for preparation')
    if args.receipt.exists():
        raise ValueError('fresh receipt required')
    if args.driver:
        protect_driver(args.driver)
    images = reference_images(args.original, args.isolated)
    args.receipt.write_text(json.dumps({'schema': 1, 'readOnlyDynamicImages': images,
        'staticFilesRemainIsolated': True}, indent=2) + '\n')
    print(f'READONLY-DYNAMIC-IMAGES {len(images)}')


if __name__ == '__main__':
    main()
