import pytest

from experiment_framework.hash_layout import UNUSED, mixed_key, parse_tables, physical_probes, replay


def snapshot(slots, count):
    return '\n'.join([
        f'STDLIB-HASH-TABLE\t0\t{2 * len(slots) + 5}\t16\t{count}',
        *(f'STDLIB-HASH-SLOT\t0\t{i}\t{key}' for i, key in enumerate(slots)),
        'STDLIB-HASH-LAYOUT-OK', 'CONTEXT-IDENTITY-OK', 'OK'])


def test_current_hash_and_exact_physical_reachability():
    key = 2163711465
    slots = [UNUSED] * 7
    home = mixed_key(key, 'original') * len(slots) >> 32
    slots[home] = key
    tables = parse_tables(snapshot(slots, 1))
    assert physical_probes(tables) == dict(keys=1, successfulMean=1, successfulMaximum=1)
    assert replay(tables, 'original')['successfulMean'] == 1
    slots[home] = UNUSED
    slots[(home - 2) % len(slots)] = key
    with pytest.raises(ValueError, match='unreachable'):
        physical_probes([slots])


@pytest.mark.parametrize('slots,count', [([1, UNUSED], 0), ([1, 1, UNUSED], 2),
                                        ([2, UNUSED], 1), ([1, 5], 2)])
def test_invalid_snapshots_do_not_enter_models(slots, count):
    with pytest.raises(ValueError):
        parse_tables(snapshot(slots, count))


def test_incomplete_snapshot_and_unknown_mixer_rejected():
    with pytest.raises(ValueError, match='complete'):
        parse_tables(snapshot([1, UNUSED], 1).replace('STDLIB-HASH-LAYOUT-OK', ''))
    with pytest.raises(ValueError, match='known offline'):
        mixed_key(1, 'unknown')
