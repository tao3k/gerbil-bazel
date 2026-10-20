"""Protocol/preflight rejection only; real compilation controls run in Bash."""
import hashlib
import os
from pathlib import Path
import subprocess
import shutil

import pytest

ROOT = Path(__file__).resolve().parents[3]
BINARY = ROOT / '.data/d1510-object-request-driver-bin-v1/gambit-file-sha256'
pytestmark = pytest.mark.skipif(not BINARY.exists(), reason='owned native batch prototype required')
MAGIC = b'gambit-native-object-batch-v3\0'


def test_polished_candidate_is_separate_and_pinned():
    stack = ROOT / 'patches/gerbil-v19-darwin'
    patches = {
        '0046-gambit-darwin-native-object-request-context.patch':
            'c98665e2b56e942624e0be7a4ea48ba1d46f4a54af632d0e40ccf4f0f2cfb23e',
        '0047-gambit-darwin-object-request-prepare-candidate.patch':
            '73088ff011836b7eaf2191db3a95002615a670679217c8c990c7f9a6a3c3dbd9',
    }
    chain = (stack / 'native-object-request-candidate.series').read_text().splitlines()
    assert chain == [
        '0044-gambit-darwin-native-object-batch-coordinator.patch',
        '0045-gambit-darwin-native-object-batch-environment.patch',
        *patches,
    ]
    frozen = (stack / 'static-c-snapshot-candidate.series').read_text().splitlines()
    assert not set(chain).intersection(frozen)
    for name, digest in patches.items():
        content = (stack / name).read_bytes()
        assert hashlib.sha256(content).hexdigest() == digest
        assert b'/Users/' not in content
        assert b'gerbil-mcp' not in content


def test_candidate_patch_replays_and_matches_coordinator(tmp_path):
    stack = ROOT / 'patches/gerbil-v19-darwin'
    patch = stack / '0044-gambit-darwin-native-object-batch-coordinator.patch'
    environment_patch = stack / '0045-gambit-darwin-native-object-batch-environment.patch'
    context_patch = stack / '0046-gambit-darwin-native-object-request-context.patch'
    original = ROOT / '.data/d1510-native-compiler-prefix-source-v1/bin/gambit-static-object-native.c'
    if not original.exists():
        pytest.skip('owned 0043 source fixture required')
    binary_sources = tmp_path / 'bin'
    binary_sources.mkdir()
    native = binary_sources / original.name
    batch = binary_sources / 'gambit-static-object-batch.c'
    shutil.copyfile(original, native)
    subprocess.run(['git', 'apply', '--check', str(patch)], cwd=tmp_path, check=True)
    subprocess.run(['git', 'apply', str(patch)], cwd=tmp_path, check=True)
    subprocess.run(['git', 'apply', '--check', str(environment_patch)], cwd=tmp_path, check=True)
    subprocess.run(['git', 'apply', str(environment_patch)], cwd=tmp_path, check=True)
    expected_native = original.read_text().replace('int main(int argc, char **argv)',
                                                  'int capture_single_main(int argc, char **argv)', 1)
    expected_native = expected_native.replace('extern char **environ;\n',
        'extern char **environ;\nstatic _Thread_local char **gambit_static_compile_environment;\n', 1)
    expected_native = expected_native.replace(
        'if (setup == 0) setup = posix_spawn(&process, arguments[0], &actions, NULL, arguments, environ);',
        'if (setup == 0) setup = posix_spawn(&process, arguments[0], &actions, NULL, arguments,\n'
        '                                    gambit_static_compile_environment ? gambit_static_compile_environment : environ);', 1)
    assert native.read_text() == expected_native + '\n#include "gambit-static-object-batch.c"\n'
    subprocess.run(['git', 'apply', '--check', str(context_patch)], cwd=tmp_path, check=True)
    subprocess.run(['git', 'apply', str(context_patch)], cwd=tmp_path, check=True)
    prototype = (stack / 'tests/native_object_batch.c').read_text()
    assert batch.read_text() == prototype.replace('#include "gambit-static-object-base.c"\n', '', 1)
    assert 'posix_spawn_file_actions_addchdir_np(&actions, gambit_static_compile_directory)' in native.read_text()
    assert 'normalize_input(input, normalized, pin, display)' in native.read_text()
    subprocess.run(['git', 'apply', '--reverse', str(context_patch)], cwd=tmp_path, check=True)
    assert native.read_text() == expected_native + '\n#include "gambit-static-object-batch.c"\n'
    subprocess.run(['git', 'apply', '--reverse', str(environment_patch)], cwd=tmp_path, check=True)
    subprocess.run(['git', 'apply', '--reverse', str(patch)], cwd=tmp_path, check=True)
    assert not batch.exists()
    assert native.read_bytes() == original.read_bytes()


def test_prepare_patch_replays_and_matches_helper(tmp_path):
    fixture = ROOT / '.data/d1510-object-request-driver-patch-v1'
    if not fixture.exists():
        pytest.skip('owned configured driver fixture required')
    original = subprocess.check_output(
        ['git', 'show', ':bin/gambuild-C.unix.in'], cwd=fixture,
    )
    directory = tmp_path / 'bin'
    directory.mkdir()
    driver = directory / 'gambuild-C.unix.in'
    driver.write_bytes(original)
    stack = ROOT / 'patches/gerbil-v19-darwin'
    patch = stack / '0047-gambit-darwin-object-request-prepare-candidate.patch'
    subprocess.run(['git', 'apply', '--check', str(patch)], cwd=tmp_path, check=True)
    subprocess.run(['git', 'apply', str(patch)], cwd=tmp_path, check=True)
    helper = directory / 'gambit-object-request-prepare'
    assert helper.read_bytes() == (stack / 'tests/gambit-object-request-prepare.unix').read_bytes()
    subprocess.run(['sh', '-n', str(driver)], check=True)
    subprocess.run(['sh', '-n', str(helper)], check=True)
    assert 'elif test "${GAMBIT_DARWIN_STATIC_OBJECT_REUSE-}" = 1' in driver.read_text()
    subprocess.run(['git', 'apply', '--reverse', str(patch)], cwd=tmp_path, check=True)
    assert driver.read_bytes() == original
    assert not helper.exists()


@pytest.mark.parametrize('control', [
    'disabled', 'truncated', 'duplicate', 'source-target-alias',
    'manifest-target-alias', 'wrong-cwd', 'unsupported-debug', 'invalid-workers',
    'old-protocol', 'duplicate-environment', 'truncated-environment',
    'environment-text-mismatch', 'multiline-environment',
])
def test_batch_preflight_rejects_without_publication(tmp_path, control):
    source = tmp_path / 'source.c'
    source.write_bytes(b'int value(void) { return 17; }\n')
    environment = tmp_path / 'environment'
    environment.write_bytes(b'PATH=/usr/bin:/bin\n')
    raw_environment = tmp_path / 'environment.nul'
    raw_environment.write_bytes(b'PATH=/usr/bin:/bin\0')
    manifest = tmp_path / 'request'
    target = tmp_path / 'result.o'
    stage = tmp_path / 'stage'
    arguments = [''] * 27
    arguments[1] = '--capture'
    arguments[2] = str(source)
    arguments[3] = str(target)
    arguments[6] = hashlib.sha256(source.read_bytes()).hexdigest()
    arguments[8] = str(tmp_path)
    arguments[9] = str(environment)
    arguments[25] = str(raw_environment)
    arguments[26] = 'source.c'
    if control == 'source-target-alias':
        arguments[3] = str(source)
    elif control == 'manifest-target-alias':
        arguments[3] = str(manifest)
    elif control == 'wrong-cwd':
        arguments[8] = '/'
    elif control == 'unsupported-debug':
        arguments[14] = '-g'
    elif control == 'duplicate-environment':
        raw_environment.write_bytes(b'PATH=/usr/bin:/bin\0PATH=/tmp\0')
    elif control == 'truncated-environment':
        raw_environment.write_bytes(b'PATH=/usr/bin:/bin')
    elif control == 'environment-text-mismatch':
        raw_environment.write_bytes(b'PATH=/tmp\0')
    elif control == 'multiline-environment':
        raw_environment.write_bytes(b'PATH=/usr/bin\nOTHER=1\0')
    record = b''.join(value.encode() + b'\0' for value in arguments)
    data = MAGIC + record
    if control == 'duplicate':
        data += record
    elif control == 'truncated':
        data = data[:-1]
    elif control == 'old-protocol':
        data = data.replace(MAGIC, b'gambit-native-object-batch-v1\0', 1)
    manifest.write_bytes(data)
    env = dict(os.environ, GAMBIT_DARWIN_NATIVE_OBJECT_BATCH='1')
    if control == 'disabled':
        env.pop('GAMBIT_DARWIN_NATIVE_OBJECT_BATCH')
    result = subprocess.run(
        [str(BINARY), '--batch', str(manifest), str(stage),
         '0' if control == 'invalid-workers' else '2'],
        cwd=tmp_path, env=env, capture_output=True, timeout=3,
    )
    assert result.returncode == (77 if control in ('disabled', 'old-protocol') else 2)
    assert not stage.exists()
    assert not target.exists()
    assert manifest.read_bytes() == data
    assert source.read_bytes() == b'int value(void) { return 17; }\n'
    assert not list(tmp_path.glob('*.gambit-static-lock'))
