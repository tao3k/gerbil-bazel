from pathlib import Path

import pytest

from gambit_hash_cold_tail import GUARD, transform
from experiment_framework.spawn import HASH_CASES, semantic_admission


def source():
    root = Path(__file__).resolve().parents[3]
    return (root / '.data/d1391-runtime-object-source/src/gambit/lib/mem.c').read_text()


def test_only_rehash_boundary_changes():
    text = source()
    result = transform(text)
    assert result.count('__attribute__((musttail)) return') == 4
    assert result.count('#if ' + GUARD) == 6
    for name in ('ref', 'set'):
        begin = text.index('___SCMOBJ ___gc_hash_table_' + name + '\n')
        end = text.index('\n}\n', begin) + 3
        old = text[begin:end]
        start = result.index('___SCMOBJ ___gc_hash_table_' + name + '\n')
        stop = result.index('\n}\n', start) + 3
        new = result[start:stop]
        tail = old.split('#endif\n', 1)[1]
        assert new.endswith(tail)


def test_changed_source_envelope_rejected():
    with pytest.raises(ValueError):
        transform(source().replace('    gc_hash_table_rehash_in_situ (ht);', '    abort();'))


def test_semantic_inventory_is_exact_and_not_speed_admission():
    text = '\n'.join('CASE-OK ' + name for name in HASH_CASES) + '\nOK hash-cold-tail-semantics\n'
    assert semantic_admission(text, True, True, 'hash-cold-tail')
    assert not semantic_admission(text + 'CASE-OK missing\n', True, True, 'hash-cold-tail')
    assert not semantic_admission(text.replace('CASE-OK missing\n', ''), True, True, 'hash-cold-tail')
    assert not semantic_admission(text, True, False, 'hash-cold-tail')
    assert not semantic_admission(text, False, True, 'hash-cold-tail')
    with pytest.raises(ValueError):
        semantic_admission(text, True, True, 'unknown')
