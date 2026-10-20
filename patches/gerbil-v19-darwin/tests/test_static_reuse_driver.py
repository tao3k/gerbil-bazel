import pytest

from prepare_static_reuse_driver import inject, native_hash, helper_source
from pathlib import Path
import hashlib
import json


def test_native_hash_binds_the_new_backend_and_guards_darwin():
    source = Path(__file__).with_name('gambit-static-object-reuse-v3.unix').read_text()
    transformed = native_hash(source)
    assert '/usr/bin/shasum' not in transformed
    assert 'gambit-file-sha256" --raw "$1"' in transformed
    assert '!= Darwin' in transformed
    assert '"$(dirname "$0")/gambit-file-sha256"\n' in transformed
    assert 'tools.compiled' in transformed and 'tools.hit' in transformed


def test_native_hash_rejects_source_drift():
    with pytest.raises(ValueError):
        native_hash('unrecognized helper')


def test_reuse_is_opt_in_and_retains_original_command():
    result = inject('before\n    eval "${BUILD_OBJ_CMD}"\nafter\n')
    assert result.startswith('before\n') and result.endswith('after\n')
    assert 'GAMBIT_DARWIN_STATIC_OBJECT_REUSE-' in result
    assert result.count('eval "${BUILD_OBJ_CMD}"') == 1


def test_source_drift_is_rejected():
    with pytest.raises(ValueError):
        inject('no matching branch')
    with pytest.raises(ValueError):
        inject('    eval "${BUILD_OBJ_CMD}"\n' * 2)


def test_native_preparation_default_reproduces_measured_helper_bytes():
    path = helper_source(Path('native-backend'))
    checkpoint = json.loads((Path(__file__).parent.parent / 'receipts/d1510-static-object-reuse-v4-checkpoint.json').read_text())
    assert hashlib.sha256(native_hash(path.read_text()).encode()).hexdigest() == checkpoint['helperSha256']
    assert helper_source(None).name == 'gambit-static-object-reuse.unix'
    supplied = Path('explicit-helper')
    assert helper_source(Path('native-backend'), supplied) == supplied
