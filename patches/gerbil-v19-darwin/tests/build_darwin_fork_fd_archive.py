"""Private C-only consumer archive; never replace the frozen HOME or Scheme IO."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

from bazel_host_environment import build_environment
from verify_reader_batch_50_baseline import main as verify


def digest(data):
    return hashlib.sha256(data).hexdigest()


def members(archive, env):
    names = subprocess.check_output(['/usr/bin/ar', '-t', str(archive)], env=env,
                                    timeout=10).decode().splitlines()
    names = [name for name in names if not name.startswith('__.SYMDEF')]
    if len(names) != len(set(names)) or names.count('os_io.o') != 1:
        raise ValueError('archive member identity is ambiguous')
    return {name: digest(subprocess.check_output(
        ['/usr/bin/ar', '-p', str(archive), name], env=env, timeout=10)) for name in names}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    out = args.output.resolve()
    if os.uname().sysname != 'Darwin' or not out.is_relative_to(root / '.data') or out.exists():
        parser.error('fresh isolated Darwin output required')
    verify()
    runtime = root / '.data/d1510-fork-fd-runtime-v1'
    construction = json.loads((runtime / 'report.json').read_text())
    obj = runtime / 'os_io_fd.o'
    if not construction['qualified'] or digest(obj.read_bytes()) != construction['forkObjectSha256']:
        raise ValueError('C-only replacement provenance mismatch')
    home = root / '.data/d1391-runtime-object-source/build'
    original = home / 'lib/libgambit.a'
    original_hash = digest(original.read_bytes())
    env = build_environment()
    before = members(original, env)
    out.mkdir()
    lib = out / 'lib'
    lib.mkdir()
    for entry in (home / 'lib').iterdir():
        if entry.name != 'libgambit.a':
            (lib / entry.name).symlink_to(entry)
    replacement = out / 'os_io.o'
    shutil.copyfile(obj, replacement)
    archive = lib / 'libgambit.a'
    shutil.copyfile(original, archive)
    subprocess.run(['/usr/bin/ar', '-r', str(archive), str(replacement)], env=env,
                   check=True, timeout=10)
    subprocess.run(['/usr/bin/ranlib', str(archive)], env=env, check=True, timeout=10)
    after = members(archive, env)
    changed = [name for name in before if before[name] != after.get(name)]
    if before.keys() != after.keys() or changed != ['os_io.o']:
        raise ValueError('replacement changes more than the C process object')
    if after['os_io.o'] != digest(obj.read_bytes()) or digest(original.read_bytes()) != original_hash:
        raise ValueError('replacement or original archive drift')
    verify()
    report = dict(constructionQualified=True, consumerLinked=False, performanceAdmitted=False,
                  testQualified=False, productionAdmitted=False, changedMembers=changed,
                  originalArchiveSha256=original_hash, archiveSha256=digest(archive.read_bytes()),
                  memberHashes=after, replacementSha256=after['os_io.o'],
                  runtimeHomeChanged=False, schemeReaderChanged=False)
    (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({key: value for key, value in report.items() if key != 'memberHashes'}))


if __name__ == '__main__':
    main()
