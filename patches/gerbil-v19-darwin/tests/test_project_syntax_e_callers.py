import pytest

from project_syntax_e_callers import rewrite


def definition(name, use_tail=False):
    result = 'tail' if use_tail else 'head'
    return (f'(define {name} (lambda (x) '
            '(let ((pair (gx#syntax-e x))) '
            f'(let ((head (##car pair)) (tail (##cdr pair))) {result}))))')


def test_only_the_two_exact_unused_tail_sites_are_rewritten():
    source = definition('gx#core-expand1') + definition('gx#core-expand-head')
    output, changes = rewrite(source)
    assert len(changes) == 2 and output.count('(projection/car x)') == 2
    assert '(##cdr pair)' not in output


def test_live_tail_and_missing_hotspot_are_refused():
    for source in (definition('gx#core-expand1'),
                   definition('gx#core-expand1', True) + definition('gx#core-expand-head')):
        with pytest.raises(ValueError, match='exact two'):
            rewrite(source)


def test_literal_lisp_symbols_and_brackets_are_not_converted():
    source = definition('gx#core-expand1') + definition('gx#core-expand-head')
    output, _ = rewrite(source + "(define literal '(t nil [expr]))")
    assert "'(t nil [expr])" in output


def test_scheme_character_literals_are_refused_not_silently_changed():
    with pytest.raises(ValueError, match='native reader'):
        rewrite(definition('gx#core-expand1') + definition('gx#core-expand-head')
                + "(define character '#\\#)")
