"""Replay and conservative protocol controls for the Darwin native backend."""
from pathlib import Path
import shutil
import subprocess

import pytest

STACK = Path(__file__).resolve().parent.parent
ROOT = STACK.parents[1]
SOURCE = ROOT / '.data/d1510-native-compiler-prefix-source-v1'
PATCH = STACK / '0043-gambit-darwin-native-compiler-prefix-flags.patch'


@pytest.mark.skipif(not SOURCE.exists(), reason='owned native source fixture required')
def test_compiler_prefix_patch_replays_exact_sources(tmp_path):
    names = ['gambit-static-object-native.c', 'gambit-static-object-reuse.unix']
    target = tmp_path / 'bin'
    target.mkdir()
    for name in names:
        shutil.copyfile(SOURCE / 'original' / name, target / name)
    subprocess.run(['git', 'apply', '--check', str(PATCH)], cwd=tmp_path, check=True)
    subprocess.run(['git', 'apply', str(PATCH)], cwd=tmp_path, check=True)
    for name in names:
        assert (target / name).read_bytes() == (SOURCE / 'bin' / name).read_bytes()
    subprocess.run(['sh', '-n', str(target / names[1])], check=True)
    subprocess.run(['git', 'apply', '--reverse', str(PATCH)], cwd=tmp_path, check=True)
    for name in names:
        assert (target / name).read_bytes() == (SOURCE / 'original' / name).read_bytes()


@pytest.mark.skipif(not SOURCE.exists(), reason='owned GNU native helper required')
@pytest.mark.parametrize('protocol', ['old', 'complex-prefix'])
def test_unrepresentable_protocol_returns_validated_fallback(protocol):
    binary = SOURCE / 'installed/bin/gambit-file-sha256'
    arguments = ['--capture'] + ['unused'] * 22
    if protocol == 'complex-prefix':
        arguments.append('-DVALUE="complex"')
        arguments[22] = ('${C_COMPILER} ${FLAGS_OPT} ${FLAGS_OBJ} ${DEFS_OBJ} '
                         '-I"${GAMBITDIR_INCLUDE}" -c -o ${BUILD_OBJ_OUTPUT_FILENAME_PARAM} '
                         '${BUILD_OBJ_CC_OPTIONS_PARAM} ${BUILD_OBJ_INPUT_FILENAMES_PARAM}')
    result = subprocess.run([str(binary), *arguments], capture_output=True, timeout=5)
    assert result.returncode == 77
