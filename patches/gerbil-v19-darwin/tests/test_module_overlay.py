import pytest

from experiment_framework.module_overlay import module_overlay_identity


@pytest.fixture
def overlay(tmp_path):
    library = tmp_path / 'lib'
    (library / 'std').mkdir(parents=True)
    (library / 'static').mkdir()
    for name in ('std/make.ssi', 'std/make.o1', 'std/make~0.o1', 'static/std__make.scm'):
        (library / name).write_bytes(name.encode())
    return library


def test_overlay_identity_binds_every_module_file(overlay):
    identity = module_overlay_identity(overlay, 'std/make')
    assert len(identity) == 4
    (overlay / 'std/make~0.o1').write_bytes(b'changed')
    assert module_overlay_identity(overlay, 'std/make') != identity


def test_debug_symbol_bundle_is_not_a_loadable_module(overlay):
    identity = module_overlay_identity(overlay, 'std/make')
    symbols = overlay / 'std/make~0.o1.dSYM'
    symbols.mkdir()
    (symbols / 'symbols').write_bytes(b'debug only')
    assert module_overlay_identity(overlay, 'std/make') == identity
    symbols.rename(overlay / 'debug-original')
    symbols.symlink_to(overlay / 'debug-original', target_is_directory=True)
    with pytest.raises(ValueError):
        module_overlay_identity(overlay, 'std/make')


@pytest.mark.parametrize('kind', ['interface', 'image', 'file-symlink', 'directory-symlink', 'traversal'])
def test_overlay_invalid_inputs_rejected(overlay, kind):
    module = 'std/make'
    if kind == 'interface':
        (overlay / 'std/make.ssi').unlink()
    elif kind == 'image':
        for path in (overlay / 'std').glob('*.o1'):
            path.unlink()
    elif kind == 'file-symlink':
        (overlay / 'std/make.o1').unlink()
        (overlay / 'std/make.o1').symlink_to(overlay / 'std/make~0.o1')
    elif kind == 'directory-symlink':
        (overlay / 'std').rename(overlay / 'original')
        (overlay / 'std').symlink_to(overlay / 'original', target_is_directory=True)
    else:
        module = '../std/make'
    with pytest.raises(ValueError):
        module_overlay_identity(overlay, module)
