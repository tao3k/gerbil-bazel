import pytest
from generate_mark_fold import generate

SOURCE = '''(define gx#stx-wrap
 (lambda (value marks) (foldl__0 (lambda (m v) (gx#stx-apply-mark v m)) value marks)))
(define gx#stx-apply-mark
 (lambda (value mark) (##structure gx#syntax-wrap::t value (gx#stx-source value) mark)))
(define gx#stx-source (lambda (value) (if (##structure? value) (##car value) '#f)))'''


def test_keeps_all_construction_and_exact_original_fallback():
    rewritten, prefix = generate(SOURCE)
    assert rewritten.count('##structure gx#syntax-wrap::t') == 1
    assert '(foldl__0 (lambda (m v) (gx#stx-apply-mark v m)) value marks)' in rewritten
    assert '(mark-fold-loop mark-fold-next mark-fold-result)' in rewritten
    assert '(##global-var-ref mark-fold-global-1)' in rewritten
    assert "(##make-global-var '__foldl1)" in prefix


def test_only_canonical_callback_and_source_read_are_accepted():
    with pytest.raises(ValueError):
        generate(SOURCE.replace('(gx#stx-apply-mark v m)', '(unknown v m)'))
    with pytest.raises(ValueError):
        generate(SOURCE.replace('(gx#stx-source value)', '(gx#stx-source (unknown value))'))


def test_native_guard_is_darwin_gnu_only():
    rewritten, prefix = generate(SOURCE)
    assert 'defined(__APPLE__) && defined(__MACH__)' in prefix
    assert '!defined(__clang__)' in prefix
    assert '(define mark-fold-native-enabled? (mark-fold-native-platform?))' in prefix
    assert '(mark-fold-native-platform?)' not in rewritten
