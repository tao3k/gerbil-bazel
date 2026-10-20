"""Prepare an isolated opt-in driver from the retained command-substitution line."""
import argparse
from pathlib import Path
import shutil

from experiment_framework.context import data_path, retained_47


def inject(source):
    anchor = '    eval "${BUILD_OBJ_CMD}"\n'
    if source.count(anchor) != 1:
        raise ValueError('one original object command required')
    return source.replace(anchor, '''    if test "${GAMBIT_DARWIN_STATIC_OBJECT_REUSE-}" = 1; then
      . "$(dirname "$0")/gambit-static-object-reuse"
      gambuild_obj_with_static_reuse
    else
      eval "${BUILD_OBJ_CMD}"
    fi
''', 1)


def native_hash(source):
    edits = {
        'digest=$(/usr/bin/shasum -a 256 "$1")':
            'digest=$("$(dirname "$0")/gambit-file-sha256" --raw "$1")',
        '/usr/bin/shasum -a 256 "$compiler"':
            '"$(dirname "$0")/gambit-file-sha256" "$compiler"',
        '"$(dirname "$0")/gambit-static-object-reuse"\n':
            '"$(dirname "$0")/gambit-static-object-reuse" "$(dirname "$0")/gambit-file-sha256"\n',
        'gambuild_obj_with_static_reuse()\n(\n':
            '''gambuild_obj_with_static_reuse()
(
  if test "$(uname -s)" != Darwin; then
    eval "$BUILD_OBJ_CMD"
    return $?
  fi
''',
    }
    for anchor, replacement in edits.items():
        if source.count(anchor) != 1:
            raise ValueError('native hash helper anchor drift')
        source = source.replace(anchor, replacement, 1)
    return source


def helper_source(native_sha, selected=None):
    if selected is not None:
        return selected
    name = 'gambit-static-object-reuse-v3.unix' if native_sha else 'gambit-static-object-reuse.unix'
    return Path(__file__).with_name(name)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--helper', type=Path)
    parser.add_argument('--native-sha', type=Path)
    parser.add_argument('--generated-c', action='store_true')
    args = parser.parse_args()
    if args.generated_c and not args.native_sha:
        parser.error('--generated-c requires --native-sha')
    root = Path(__file__).resolve().parents[3]
    tools = retained_47(root)
    output = data_path(root, args.output, fresh=True)
    output.mkdir(parents=True)
    for tool in ('gsc', 'gxi', 'gerbil'):
        (output / tool).symlink_to(tools.home / 'bin' / tool)
    original = root / '.data/d1510-shell-substitution/bin/gambuild-C'
    driver = output / 'gambuild-C'
    driver.write_text(inject(original.read_text()))
    driver.chmod(0o755)
    helper = helper_source(args.native_sha, args.helper).read_text()
    if args.native_sha:
        helper = native_hash(helper)
        shutil.copy2(args.native_sha, output / 'gambit-file-sha256')
    (output / 'gambit-static-object-reuse').write_text(helper)
    if args.generated_c:
        (output / 'gsc').rename(output / 'gsc-original')
        source_dir = Path(__file__).parent
        shutil.copy2(source_dir / 'gambit-generated-c-dispatch.sh', output / 'gsc')
        (output / 'gsc').chmod(0o755)
        for name in ('gambit-generated-c-reads.scm', 'gambit-generated-c-closure.scm',
                     'gambit-generated-c-adapter.scm'):
            shutil.copy2(source_dir / name, output / name)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
