import pytest
from gambit_allocation_sites import instrument, parse_counts, summarize_counts


SOURCE = '#include "gambit.h"\n___BEGIN_ALLOC_STRUCTURE(4UL)\n___END_ALLOC_STRUCTURE(4)\n'


def test_instrumentation_retains_original_body_and_line_numbers():
    result = instrument(SOURCE)
    assert '#line 2\n' in result
    assert result.endswith(SOURCE.split('\n', 1)[1])
    assert '___hp += gb_n' in result
    assert '___MAX_PROCESSORS != 1' in result
    assert 'fopen(path, "wx")' in result


def test_parse_physical_words_without_accounting_metric_conversion():
    assert parse_counts('ERRORS 0\n3 10 50\n', SOURCE) == [
        dict(line=3, calls=10, physicalWords=50)]


@pytest.mark.parametrize('macro', ['___CONS(a,b)', '___MAKECONTINUATION(a,b)', '___F64BOX(a)', '___ALLOC_CLO(2UL)'])
def test_nested_allocator_macros(macro):
    source = '#include "gambit.h"\n___SET_R1(' + macro + ')\n'
    assert parse_counts('ERRORS 0\n2 1 3\n', source)[0]['physicalWords'] == 3


def test_procedure_summary_preserves_site_counts():
    source = '#define ___PH_PROC A\n___BEGIN_P_SW\n___CONS(a,b)\n___END_P_SW\n#define ___PH_PROC B\n___BEGIN_P_SW\n___ALLOC_CLO(1)\n___END_P_SW\n'
    rows = parse_counts('ERRORS 0\n3 3 9\n7 2 6\n', source)
    summary = summarize_counts(rows, source)
    assert summary == dict(physicalWords=15, allocationCalls=5,
                          byProcedure={'A': dict(calls=3, physicalWords=9),
                                       'B': dict(calls=2, physicalWords=6)})
    with pytest.raises(ValueError):
        summarize_counts([dict(line=1, calls=1, physicalWords=3)], '___CONS(a,b)')


@pytest.mark.parametrize('text', ['', 'ERRORS 1\n2 1 5\n', 'ERRORS 0\n',
                                'ERRORS 0\n2 1 5\n2 1 5\n', 'ERRORS 0\n2 3 2\n',
                                'ERRORS 0\n1 1 5\n', 'ERRORS 0\n2 1 5\n'])
def test_invalid_or_unreached_counts_are_rejected(text):
    with pytest.raises(ValueError):
        parse_counts(text, SOURCE)


@pytest.mark.parametrize('source', ['', SOURCE + SOURCE, SOURCE + '#line 99\n'])
def test_ambiguous_source_is_rejected(source):
    with pytest.raises(ValueError):
        instrument(source)
