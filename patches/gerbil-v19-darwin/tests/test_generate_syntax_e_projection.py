import pytest
from sexpdata import loads

from generate_syntax_e_projection import dump, generate

SOURCE = ('(define gx#syntax-e (lambda (x) (if (pair? x) '
          '(cons (gx#stx-wrap (car x) marks) (gx#stx-wrap (cdr x) marks)) x)))')


def test_keeps_both_effectful_computations_in_order():
    output = generate(SOURCE)
    assert output.count('(gx#stx-wrap (car x) marks)') == 2
    assert output.count('(gx#stx-wrap (cdr x) marks)') == 2
    assert '(let* ((projection-head' in output
    assert '(eq? (##global-var-ref projection-global-4) projection-original-4)' in output
    assert '(eq? (##global-var-ref projection-global-1) projection-original-1)' in output
    assert '(car ((##global-var-ref projection-global-0) stx))' in output
    assert loads('(' + output + ')')


def test_unknown_constructor_and_duplicate_definition_are_rejected():
    with pytest.raises(ValueError):
        generate(SOURCE.replace('gx#stx-wrap', 'unknown'))
    with pytest.raises(ValueError):
        generate(SOURCE + SOURCE)


def test_scheme_symbols_and_quoted_false_round_trip():
    value = loads("(gx#syntax-e '##foo '#f \"value\")")
    assert loads(dump(value)) == value


def test_native_guard_is_darwin_gnu_only():
    output = generate(SOURCE, native_guard=True)
    assert 'defined(__APPLE__) && defined(__MACH__)' in output
    assert 'defined(__GNUC__) && !defined(__clang__)' in output
    assert '(projection-native-platform?)' in output


def test_field_elimination_is_explicit_and_guards_fold_and_callback():
    ordinary = generate(SOURCE)
    specialized = generate(SOURCE, discard_unused_field=True)
    assert ordinary.count('(gx#stx-wrap (car x) marks)') == 2
    assert specialized.count('(gx#stx-wrap (car x) marks)') == 1
    assert specialized.count('(gx#stx-wrap (cdr x) marks)') == 1
    assert "(##make-global-var 'gx#stx-apply-mark)" in specialized
    assert "(##make-global-var '__foldl1)" in specialized
    assert '(let* ((projection-head' not in specialized
