import hashlib
import json

import pytest

from native_generated_c_profile import verify_native_profile, verify_build_lock


@pytest.fixture
def native_profile(tmp_path):
    root = tmp_path
    driver = root / '.data/native/bin'
    stack = root / 'patches/gerbil-v19-darwin'
    driver.mkdir(parents=True)
    (driver.parent / 'gsc').mkdir()
    (stack / 'tests').mkdir(parents=True)
    (stack / 'receipts').mkdir()
    lock = dict(files={}, sources={}, entrySources={})
    for name, data in [('gsc', b'native'), ('gsc-original', b'original')]:
        (driver / name).write_bytes(data)
        lock['files'][name] = hashlib.sha256(data).hexdigest()
    data = b'native hook source'
    for path in (stack / 'tests/hook.scm', driver.parent / 'gsc/hook.scm'):
        path.write_bytes(data)
    lock['sources']['hook.scm'] = hashlib.sha256(data).hexdigest()
    (stack / 'receipts/d1510-native-generated-c-profile-v8.json').write_text(json.dumps(lock))
    return root, driver


def test_exact_native_profile_admitted(native_profile):
    root, driver = native_profile
    assert verify_native_profile(root, driver)['gsc'] == hashlib.sha256(b'native').hexdigest()


@pytest.mark.parametrize('changed', ['none', 'no-digests', 'planned', 'no-runtime', 'drift'])
def test_closed_link_is_explicit_and_runtime_bound(native_profile, changed):
    root, driver = native_profile
    receipts = root / 'patches/gerbil-v19-darwin/receipts'
    path = receipts / 'closed-link.json'
    lock = json.loads((receipts / 'd1510-native-generated-c-profile-v8.json').read_text())
    runtime = root / '.data/runtime'
    runtime.mkdir()
    archive = runtime / 'archive'
    archive.write_bytes(b'matching ABI')
    lock['runtimeFiles'] = {'archive': hashlib.sha256(archive.read_bytes()).hexdigest()}
    path.write_text(json.dumps(lock))
    if changed == 'drift':
        archive.write_bytes(b'other ABI')
    arguments = dict(in_process_digests=changed != 'no-digests',
                     planned_producers=changed == 'planned', closed_link_profile=path,
                     runtime=None if changed == 'no-runtime' else runtime)
    if changed == 'none':
        assert verify_native_profile(root, driver, **arguments) == lock['files']
    else:
        with pytest.raises(ValueError):
            verify_native_profile(root, driver, **arguments)


def test_compiled_digest_profile_requires_explicit_selection(native_profile):
    root, driver = native_profile
    receipts = root / 'patches/gerbil-v19-darwin/receipts'
    lock = json.loads((receipts / 'd1510-native-generated-c-profile-v8.json').read_text())
    lock['files']['gsc'] = hashlib.sha256(b'compiled-digests').hexdigest()
    (receipts / 'd1510-native-generated-c-profile-v9.json').write_text(json.dumps(lock))
    with pytest.raises(ValueError):
        verify_native_profile(root, driver, in_process_digests=True)
    (driver / 'gsc').write_bytes(b'compiled-digests')
    with pytest.raises(ValueError):
        verify_native_profile(root, driver)
    assert verify_native_profile(root, driver, in_process_digests=True) == lock['files']


def test_planned_profile_cannot_inherit_old_binary_admission(native_profile):
    root, driver = native_profile
    receipts = root / 'patches/gerbil-v19-darwin/receipts'
    lock = json.loads((receipts / 'd1510-native-generated-c-profile-v8.json').read_text())
    lock['files']['gsc'] = hashlib.sha256(b'planned').hexdigest()
    (receipts / 'd1510-native-generated-c-profile-v11.json').write_text(json.dumps(lock))
    with pytest.raises(ValueError):
        verify_native_profile(root, driver, planned_producers=True)
    with pytest.raises(ValueError):
        verify_native_profile(root, driver, in_process_digests=True, planned_producers=True)
    (driver / 'gsc').write_bytes(b'planned')
    assert verify_native_profile(root, driver, in_process_digests=True, planned_producers=True) == lock['files']


@pytest.mark.parametrize('changed', ['binary', 'compiled-source', 'tracked-source', 'symlink'])
def test_native_profile_drift_rejected(native_profile, changed):
    root, driver = native_profile
    paths = dict(binary=driver / 'gsc',
                 **{'compiled-source': driver.parent / 'gsc/hook.scm',
                    'tracked-source': root / 'patches/gerbil-v19-darwin/tests/hook.scm'})
    if changed == 'symlink':
        copy = driver / 'gsc-copy'
        copy.write_bytes((driver / 'gsc').read_bytes())
        (driver / 'gsc').unlink()
        (driver / 'gsc').symlink_to(copy)
    else:
        paths[changed].write_bytes(b'changed')
    with pytest.raises(ValueError):
        verify_native_profile(root, driver)


@pytest.mark.parametrize('changed', ['none', 'runtime', 'patch', 'input', 'missing-runtime'])
def test_explicit_build_identity_binds_prerequisites(native_profile, changed):
    root, driver = native_profile
    stack = root / 'patches/gerbil-v19-darwin'
    runtime = root / '.data/runtime'
    runtime.mkdir()
    paths = {'runtime': runtime / 'archive', 'patch': stack / 'fix.patch',
             'input': stack / 'tests/input.scm'}
    for path in paths.values():
        path.write_bytes(b'bound prerequisite')
    lock_path = stack / 'receipts/d1510-native-generated-c-profile-v8.json'
    lock = json.loads(lock_path.read_text())
    digest = hashlib.sha256(b'bound prerequisite').hexdigest()
    lock.update(runtimeFiles={'archive': digest}, patches={'fix.patch': digest},
                inputs={'input.scm': digest})
    lock_path.write_text(json.dumps(lock))
    if changed in paths:
        paths[changed].write_bytes(b'drift')
    if changed == 'none':
        assert verify_build_lock(root, driver, lock_path, runtime) == lock['files']
    else:
        with pytest.raises(ValueError):
            verify_build_lock(root, driver, lock_path, None if changed == 'missing-runtime' else runtime)
