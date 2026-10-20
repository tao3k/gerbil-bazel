import pytest

from experiment_framework.static_reuse_trace import FIELDS, compare_traces, read_traces


def trace(directory, values=None):
    directory.mkdir()
    fields = dict.fromkeys(FIELDS, 'a' * 64)
    fields.update(values or {})
    path = directory / 'module.o.gambit-static-key-trace'
    path.write_text(''.join(f'{key} {value}\n' for key, value in sorted(fields.items())))
    return path


def test_component_changes_are_not_conflated(tmp_path):
    before, after = tmp_path / 'before', tmp_path / 'after'
    trace(before)
    trace(after, dict(environment='b' * 64, key='c' * 64))
    result = compare_traces(before, after)
    assert result['objects'] == 1
    assert result['changedCounts'] == dict(source=0, cpp=0, environment=1,
                                         tools=0, **{'command-cwd': 0, 'key': 1})


@pytest.mark.parametrize('mutation', ['empty', 'missing-field', 'duplicate', 'malformed', 'symlink'])
def test_incomplete_or_redirected_evidence_is_denied(tmp_path, mutation):
    root = tmp_path / 'traces'
    path = trace(root)
    if mutation == 'empty':
        path.unlink()
    elif mutation == 'missing-field':
        path.write_text('key ' + 'a' * 64 + '\n')
    elif mutation == 'duplicate':
        path.write_text(path.read_text() + 'key ' + 'a' * 64 + '\n')
    elif mutation == 'malformed':
        path.write_text('key not-a-digest\n')
    else:
        target = tmp_path / 'target'
        path.rename(target)
        path.symlink_to(target)
    with pytest.raises(ValueError):
        read_traces(root)


def test_inventory_drift_is_denied(tmp_path):
    before, after = tmp_path / 'before', tmp_path / 'after'
    trace(before)
    path = trace(after)
    path.rename(after / 'different.o.gambit-static-key-trace')
    with pytest.raises(ValueError, match='inventories'):
        compare_traces(before, after)
