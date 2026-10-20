from pathlib import Path
import json
import pytest

from experiment_framework.ascent_profile import install_module_overlay, protect_driver, reference_images, verify_images


def test_both_native_image_versions_reference_exact_original_bytes(tmp_path):
    original, isolated = tmp_path / 'original', tmp_path / 'isolated'
    original.mkdir()
    isolated.mkdir()
    for name in ('module.o1', 'module.o2'):
        (original / name).write_bytes(name.encode())
        (isolated / name).write_bytes(name.encode())
    (isolated / 'module.o').write_bytes(b'owned static')
    records = reference_images(original, isolated, ('.o1', '.o2'))
    assert len(records) == 2
    for name in ('module.o1', 'module.o2'):
        assert (isolated / name).is_symlink()
        assert (isolated / name).read_bytes() == (original / name).read_bytes()
    assert not (isolated / 'module.o').is_symlink()


def test_only_identical_dynamic_images_are_referenced(tmp_path):
    original, isolated = tmp_path / 'original', tmp_path / 'isolated'
    original.mkdir()
    isolated.mkdir()
    for root in (original, isolated):
        (root / 'module.o1').write_bytes(b'dynamic')
        (root / 'module.o').write_bytes(b'static')
        (root / 'module.c').write_bytes(b'source')
    receipt = reference_images(original, isolated)
    assert len(receipt) == 1
    assert (isolated / 'module.o1').resolve() == original / 'module.o1'
    assert not (isolated / 'module.o').is_symlink()
    assert not (isolated / 'module.c').is_symlink()
    assert (original / 'module.o1').read_bytes() == b'dynamic'
    stored = tmp_path / 'receipt.json'
    stored.write_text(json.dumps({'readOnlyDynamicImages': receipt}))
    assert verify_images(isolated, stored) == 1
    (original / 'module.o1').write_bytes(b'drift')
    with pytest.raises(ValueError, match='image drift'):
        verify_images(isolated, stored)


def test_mismatch_fails_before_replacing_any_image(tmp_path):
    original, isolated = tmp_path / 'original', tmp_path / 'isolated'
    original.mkdir()
    isolated.mkdir()
    (original / 'module.o1').write_bytes(b'original')
    (isolated / 'module.o1').write_bytes(b'changed')
    with pytest.raises(ValueError, match='identity drift'):
        reference_images(original, isolated)
    assert not (isolated / 'module.o1').is_symlink()


def test_driver_refuses_symlink_outputs(tmp_path):
    driver = tmp_path / 'driver'
    driver.write_text('case "$1" in\n\n  "obj")\n echo original\n ;;\nesac\n')
    protect_driver(driver)
    assert 'test -L "$isolation_output"' in driver.read_text()
    assert driver.read_text().count('echo original') == 1


def test_owned_overlay_never_writes_through_reference(tmp_path):
    original, isolated, library = [tmp_path / name for name in ('original', 'isolated', 'library')]
    for base in (original, isolated):
        (base / 'lib/std').mkdir(parents=True)
        (base / 'lib/std/make.o1').write_bytes(b'old module')
        (base / 'lib/std/other.o1').write_bytes(b'other')
        (base / 'lib/static').mkdir()
        (base / 'lib/static/std__make.c').write_bytes(b'stale C')
    records = reference_images(original, isolated)
    receipt = tmp_path / 'receipt.json'
    receipt.write_text(json.dumps(dict(readOnlyDynamicImages=records)))
    (library / 'std').mkdir(parents=True)
    (library / 'std/make.o1').write_bytes(b'new module')
    (library / 'std/make.ssi').write_bytes(b'interface')
    (library / 'static').mkdir()
    (library / 'static/std__make.scm').write_bytes(b'new source')
    assert install_module_overlay(isolated, library, 'std/make', receipt) == 3
    assert verify_images(isolated, receipt) == 1
    assert (original / 'lib/std/make.o1').read_bytes() == b'old module'
    assert (original / 'lib/static/std__make.c').read_bytes() == b'stale C'
    assert not (isolated / 'lib/std/make.o1').is_symlink()
    assert not (isolated / 'lib/static/std__make.c').exists()
    (isolated / 'lib/std/make.o1').write_bytes(b'drift')
    with pytest.raises(ValueError, match='overlay drift'):
        verify_images(isolated, receipt)


def test_overlay_rejects_traversal_before_touching_receipt(tmp_path):
    receipt = tmp_path / 'receipt.json'
    with pytest.raises(ValueError, match='invalid overlay module'):
        install_module_overlay(tmp_path, tmp_path / 'library', '../make', receipt)
    assert not receipt.exists()
