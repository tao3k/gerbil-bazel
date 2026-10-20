import shutil

import pytest

from experiment_framework.source_runtime import prepare, sha, verify


@pytest.fixture
def fixture(tmp_path):
    runtime, source, output = [tmp_path / name for name in ('runtime', 'source', 'output')]
    for name in ('include/gambit.h', 'lib/libgambit.a', 'lib/libgambitgsc.a'):
        path = runtime / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(name.encode())
    path = source / 'std/example.ss'
    path.parent.mkdir(parents=True)
    path.write_text('(export example)')
    return runtime, source, output


def test_source_fixture_preserves_runtime_and_source(fixture):
    runtime, source, output = fixture
    record = prepare(runtime, source, output, shutil.copytree)
    assert not (runtime / 'src').exists()
    assert record['sourceFiles']['src/std/example.ss'] == sha(source / 'std/example.ss')
    for name, digest in record['runtimeFiles'].items():
        assert sha(runtime / name) == digest == sha(output / name)
    assert verify(output, record) == 1


@pytest.mark.parametrize('changed', ['source', 'runtime', 'parent-symlink', 'path-escape'])
def test_source_fixture_drift_rejected(fixture, changed):
    runtime, source, output = fixture
    record = prepare(runtime, source, output, shutil.copytree)
    if changed == 'source':
        (output / 'src/std/example.ss').write_text('different')
    elif changed == 'runtime':
        (output / 'lib/libgambit.a').write_bytes(b'different')
    elif changed == 'parent-symlink':
        (output / 'src/std/example.ss').unlink()
        (output / 'src/std').rmdir()
        (output / 'src/std').symlink_to(source / 'std')
    else:
        record['sourceFiles']['../outside'] = 'bad'
    with pytest.raises(ValueError):
        verify(output, record)


@pytest.mark.parametrize('mode', ['existing', 'source-symlink', 'already-source', 'overlap'])
def test_invalid_fixture_denied_before_copy(fixture, mode):
    runtime, source, output = fixture
    if mode == 'existing':
        output.mkdir()
    elif mode == 'source-symlink':
        (source / 'std/link.ss').symlink_to(source / 'std/example.ss')
    elif mode == 'already-source':
        (runtime / 'src').mkdir()
    else:
        output = runtime / 'nested'
    copies = []
    with pytest.raises(ValueError):
        prepare(runtime, source, output, lambda *args: copies.append(args))
    assert copies == []
