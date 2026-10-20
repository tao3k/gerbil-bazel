import pytest
from summarize_mcp_import_cost import subtract_nested, portable_name


def call(depth, seconds, allocation):
    return dict(depth=depth, seconds=seconds, allocatedBytes=allocation, module='test')


def test_nested_calls_are_subtracted_once_not_as_all_descendants():
    rows = subtract_nested([call(2, 1, 10), call(1, 2, 20), call(1, 3, 30), call(0, 7, 70)])
    assert [r['observedSelfSeconds'] for r in rows] == [1, 1, 3, 2]
    assert sum(r['observedSelfAllocatedBytes'] for r in rows) == 70


def test_independent_roots_do_not_subtract_each_other():
    rows = subtract_nested([call(0, 1, 10), call(0, 2, 20)])
    assert sum(r['observedSelfAllocatedBytes'] for r in rows) == 30


@pytest.mark.parametrize('rows', [[call(1, 1, 10)], [call(2, 1, 10), call(0, 2, 20)],
                                 [call(-1, 1, 10)], [call(1, 1, 20), call(0, 2, 10)]])
def test_invalid_trees_are_rejected(rows):
    with pytest.raises(ValueError):
        subtract_nested(rows)


def test_receipt_names_remove_private_root():
    assert portable_name('"/private/root/build/lib/std/io.ssi"') == 'std/io.ssi'
    with pytest.raises(ValueError):
        portable_name('"/private/root/unrelated.ssi"')
