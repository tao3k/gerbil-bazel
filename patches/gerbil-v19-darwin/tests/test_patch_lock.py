import hashlib
import json

import pytest

from experiment_framework.patch_lock import verify_patch_lock


@pytest.fixture
def locked_stack(tmp_path):
    receipts = tmp_path / 'receipts'
    receipts.mkdir()
    driver = tmp_path / 'bin'
    driver.mkdir()
    patch = tmp_path / 'change.patch'
    patch.write_bytes(b'patch bytes')
    tool = driver / 'compiler'
    tool.write_bytes(b'tool bytes')
    (tmp_path / 'locked.series').write_text('change.patch\n')
    lock = receipts / 'lock.json'
    lock.write_text(json.dumps(dict(
        series='locked.series',
        patches={'change.patch': hashlib.sha256(patch.read_bytes()).hexdigest()},
        driverFiles={'compiler': hashlib.sha256(tool.read_bytes()).hexdigest()},
    )))
    return lock, driver


def test_locked_stack_passes(locked_stack):
    lock, driver = locked_stack
    assert verify_patch_lock(lock, driver) == 1


@pytest.mark.parametrize('mutation', ['none', 'drift', 'symlink', 'unlocked'])
def test_selected_gsc_identity(locked_stack, mutation):
    lock, driver = locked_stack
    binary = driver / 'gsc'
    binary.write_bytes(b'measured GSC')
    data = json.loads(lock.read_text())
    if mutation != 'unlocked':
        data['gscSha256'] = hashlib.sha256(binary.read_bytes()).hexdigest()
    lock.write_text(json.dumps(data))
    if mutation == 'drift':
        binary.write_bytes(b'other GSC')
    elif mutation == 'symlink':
        binary.rename(driver / 'other-gsc')
        binary.symlink_to(driver / 'other-gsc')
    if mutation == 'none':
        assert verify_patch_lock(lock, driver, gsc=binary) == 1
    else:
        with pytest.raises(ValueError):
            verify_patch_lock(lock, driver, gsc=binary)


@pytest.mark.parametrize('mutation', [
    'none', 'first', 'build', 'test', 'nan', 'bool', 'files', 'cases',
    'failed', 'samples', 'limits', 'unlocked-policy',
    'status-zero', 'status-null', 'status-string',
    'passing-bool', 'passing-float', 'passing-nan', 'passing-zero',
    'files-float', 'cases-float',
])
def test_performance_is_per_sample_and_fail_closed(locked_stack, mutation):
    lock, driver = locked_stack
    limits = dict(firstLog=4.5, completeBuild=42, completeTest=97)
    policy = dict(schema='mcp-performance-lock-v1', limitsSeconds=limits,
                  completeTest=dict(files=39, cases=965))
    policy_path = lock.parent / 'policy.json'
    policy_path.write_text(json.dumps(policy))
    data = json.loads(lock.read_text())
    data.update(limitsSeconds=limits.copy(), coldSamples=[
        dict(firstCompileSeconds=4, completeBuildSeconds=37) for _ in range(3)
    ], completeTest=dict(wallSeconds=87, files=39, cases=965, passingSamples=1))
    if mutation != 'unlocked-policy':
        data['receiptFiles'] = {'policy.json': hashlib.sha256(policy_path.read_bytes()).hexdigest()}
    if mutation == 'first':
        data['coldSamples'][1]['firstCompileSeconds'] = 4.501
    elif mutation == 'build':
        data['coldSamples'][1]['completeBuildSeconds'] = 42.001
    elif mutation == 'test':
        data['completeTest']['wallSeconds'] = 97.001
    elif mutation == 'nan':
        data['coldSamples'][1]['completeBuildSeconds'] = float('nan')
    elif mutation == 'bool':
        data['coldSamples'][1]['completeBuildSeconds'] = True
    elif mutation in {'files', 'cases'}:
        data['completeTest'][mutation] -= 1
    elif mutation == 'failed':
        data['completeTest']['passed'] = False
    elif mutation.startswith('status-'):
        data['completeTest']['passed'] = {
            'status-zero': 0, 'status-null': None, 'status-string': 'true',
        }[mutation]
    elif mutation.startswith('passing-'):
        data['completeTest']['passingSamples'] = {
            'passing-bool': True, 'passing-float': 1.0,
            'passing-nan': float('nan'), 'passing-zero': 0,
        }[mutation]
    elif mutation in {'files-float', 'cases-float'}:
        key = mutation.split('-')[0]
        data['completeTest'][key] = float(data['completeTest'][key])
    elif mutation == 'samples':
        data['coldSamples'].pop()
    elif mutation == 'limits':
        data['limitsSeconds']['completeBuild'] = 70
    lock.write_text(json.dumps(data))
    if mutation == 'none':
        assert verify_patch_lock(lock, driver, performance=True) == 1
    else:
        with pytest.raises(ValueError):
            verify_patch_lock(lock, driver, performance=True)


@pytest.mark.parametrize('mutation', [
    'none', 'drift', 'missing', 'symlink', 'parent-symlink', 'root-symlink',
    'parent', 'absolute', 'empty-part', 'dot-part', 'backslash', 'unlocked',
])
def test_raw_measurements_are_fail_closed(locked_stack, tmp_path, mutation):
    lock, driver = locked_stack
    root = tmp_path / 'measurements'
    nested = root / 'run'
    nested.mkdir(parents=True)
    report = nested / 'report.json'
    report.write_bytes(b'measured report')
    data = json.loads(lock.read_text())
    names = dict(parent='../run/report.json', absolute='/run/report.json',
                 **{'empty-part': 'run//report.json', 'dot-part': 'run/./report.json',
                    'backslash': 'run\\report.json'})
    if mutation != 'unlocked':
        data['rawEvidenceFiles'] = {
            names.get(mutation, 'run/report.json'): hashlib.sha256(report.read_bytes()).hexdigest(),
        }
    lock.write_text(json.dumps(data))
    if mutation == 'drift':
        report.write_bytes(b'changed report')
    elif mutation == 'missing':
        report.unlink()
    elif mutation == 'symlink':
        report.rename(nested / 'target')
        report.symlink_to(nested / 'target')
    elif mutation in {'parent-symlink', 'root-symlink'}:
        path = nested if mutation == 'parent-symlink' else root
        target = tmp_path / 'redirected'
        path.rename(target)
        path.symlink_to(target, target_is_directory=True)
    if mutation == 'none':
        assert verify_patch_lock(lock, driver, evidence_root=root) == 1
    else:
        with pytest.raises(ValueError):
            verify_patch_lock(lock, driver, evidence_root=root)


@pytest.mark.parametrize('mutation', ['none', 'drift', 'missing', 'symlink', 'parent', 'unlocked'])
def test_selected_runtime_identity(locked_stack, tmp_path, mutation):
    lock, driver = locked_stack
    runtime = tmp_path / 'runtime'
    runtime.mkdir()
    binary = runtime / 'interpreter'
    binary.write_bytes(b'measured runtime')
    data = json.loads(lock.read_text())
    name = '../interpreter' if mutation == 'parent' else 'interpreter'
    if mutation != 'unlocked':
        data['runtimeFiles'] = {name: hashlib.sha256(binary.read_bytes()).hexdigest()}
    lock.write_text(json.dumps(data))
    if mutation == 'drift':
        binary.write_bytes(b'different runtime')
    elif mutation == 'missing':
        binary.unlink()
    elif mutation == 'symlink':
        target = runtime / 'other'
        binary.rename(target)
        binary.symlink_to(target)
    if mutation == 'none':
        assert verify_patch_lock(lock, driver, runtime) == 1
    else:
        with pytest.raises(ValueError):
            verify_patch_lock(lock, driver, runtime)


@pytest.mark.parametrize('target', ['patch', 'driver', 'series'])
def test_drift_is_denied(locked_stack, target):
    lock, driver = locked_stack
    paths = dict(patch=lock.parent.parent / 'change.patch',
                 driver=driver / 'compiler', series=lock.parent.parent / 'locked.series')
    paths[target].write_bytes(b'drift')
    with pytest.raises(ValueError):
        verify_patch_lock(lock, driver)


def test_symlink_is_denied_even_with_matching_bytes(locked_stack):
    lock, driver = locked_stack
    tool = driver / 'compiler'
    target = driver / 'other'
    tool.rename(target)
    tool.symlink_to(target)
    with pytest.raises(ValueError, match='non-symlink'):
        verify_patch_lock(lock, driver)


def test_parent_path_is_denied(locked_stack):
    lock, driver = locked_stack
    data = json.loads(lock.read_text())
    data['series'] = '../locked.series'
    lock.write_text(json.dumps(data))
    with pytest.raises(ValueError, match='filename'):
        verify_patch_lock(lock, driver)


@pytest.mark.parametrize('section', ['receiptFiles', 'sourceFiles'])
@pytest.mark.parametrize('mutation', ['drift', 'missing', 'symlink', 'parent'])
def test_linked_evidence_is_fail_closed(locked_stack, section, mutation):
    lock, driver = locked_stack
    directory = lock.parent if section == 'receiptFiles' else lock.parent.parent / 'tests'
    directory.mkdir(exist_ok=True)
    evidence = directory / 'evidence'
    evidence.write_bytes(b'locked evidence')
    data = json.loads(lock.read_text())
    name = '../evidence' if mutation == 'parent' else 'evidence'
    data[section] = {name: hashlib.sha256(evidence.read_bytes()).hexdigest()}
    lock.write_text(json.dumps(data))
    if mutation == 'drift':
        evidence.write_bytes(b'changed')
    elif mutation == 'missing':
        evidence.unlink()
    elif mutation == 'symlink':
        target = directory / 'target'
        evidence.rename(target)
        evidence.symlink_to(target)
    with pytest.raises(ValueError):
        verify_patch_lock(lock, driver)


@pytest.mark.parametrize('section', ['receiptFiles', 'sourceFiles'])
def test_linked_evidence_passes(locked_stack, section):
    lock, driver = locked_stack
    directory = lock.parent if section == 'receiptFiles' else lock.parent.parent / 'tests'
    directory.mkdir(exist_ok=True)
    evidence = directory / 'evidence'
    evidence.write_bytes(b'locked evidence')
    data = json.loads(lock.read_text())
    data[section] = {'evidence': hashlib.sha256(evidence.read_bytes()).hexdigest()}
    lock.write_text(json.dumps(data))
    assert verify_patch_lock(lock, driver) == 1
