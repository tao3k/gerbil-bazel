import pytest

from audit_syntax_e_projections import projections


def fixture(first='___SET_R1(___CAR(___R1))', extra=''):
    return ('#define ___PH_LBL0 10\n___BEGIN_P_SW\n'
            '___SET_R0(___LBL(5))\n___ADJFP(-4)\n'
            '___JUMPGLONOTSAFE(___SET_NARGS(1),778,___G_gx_23_syntax_2d_e)\n'
            '___DEF_SLBL(5,___L5_test)\n' + first + '\n' + extra +
            '\n___END_P_SW\n')


def test_immediate_car_and_cdr_are_only_opportunities():
    for field in ('CAR', 'CDR'):
        sites = projections(fixture(f'___SET_R1(___{field}(___R1))'))
        assert len(sites) == 1 and sites[0]['field'] == field
        assert sites[0]['producerSideEffectsProvenRemovable'] is False


def test_intervening_operation_is_not_an_immediate_projection():
    assert projections(fixture('___SET_STK(1,___R1)\n___SET_R1(___CAR(___R1))')) == []


def test_other_callee_and_missing_continuation_are_not_selected():
    assert projections(fixture().replace('___G_gx_23_syntax_2d_e', '___G_other')) == []
    assert projections(fixture().replace('___DEF_SLBL(5,', '___DEF_SLBL(6,')) == []


def test_duplicate_continuation_is_rejected():
    with pytest.raises(ValueError, match='ambiguous'):
        projections(fixture(extra='___DEF_SLBL(5,___L5_duplicate)'))
