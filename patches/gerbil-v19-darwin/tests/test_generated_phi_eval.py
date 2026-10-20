import pytest

from prepare_generated_phi_eval import ANCHOR, prepare


def test_exact_load_boundary_only():
    text = 'before\n' + ANCHOR + '\nafter'
    result = prepare(text)
    assert result.startswith('before\n') and result.endswith('\nafter')
    assert result.count(ANCHOR.strip()) == 1
    assert '"gambit-generated-phi-source-v1"' in result
    for guard in ('__APPLE__', '__MACH__', '__GNUC__', '!defined(__clang__)'):
        assert guard in result


@pytest.mark.parametrize('text', ['', ANCHOR + ANCHOR])
def test_ambiguous_or_missing_load_boundary_rejected(text):
    with pytest.raises(ValueError):
        prepare(text)


def test_no_global_expander_replacement_or_parameter_shortcut():
    result = prepare(ANCHOR)
    assert 'expand-source-set!' not in result
    assert '__scheme-source' not in result
    for retained in ('##in-new-compilation-ctx', '##comp-top',
                     '##extract-demand-modules', '##convert-source-to-locat!',
                     '##setup-requirements-and-run', '##top-cte-clone'):
        assert retained in result
