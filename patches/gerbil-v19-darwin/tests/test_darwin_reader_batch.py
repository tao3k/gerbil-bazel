from pathlib import Path
import pytest

from prepare_darwin_reader_batch import prepare


def original():
    root = Path(__file__).resolve().parents[3]
    return (root / '.data/d1391-runtime-object-source/src/gambit/lib/_io.scm').read_text()


def test_original_reader_is_retained_in_both_fallback_and_other_platform_branch():
    result = prepare(original())
    assert '(or (##gb-darwin-buffered-token re c i)' in result
    assert '(else\n  (let loop ((i i))' in result
    assert result.count('string-set! s i next') == original().count('string-set! s i next') + 1


def test_ambiguity_is_rejected():
    with pytest.raises(ValueError):
        prepare(original() + '\n(define (##build-delimited-string re c i)\n')


def test_lock_cursor_and_buffer_validation_precede_consumption():
    text = Path(__file__).with_name('darwin_reader_batch_helper.scm').read_text()
    assert text.count('___PRIMITIVETRYLOCK') == 2
    assert text.count('___PRIMITIVEUNLOCK') == 2
    assert text.count('___PORT_CHAR_RBUF_FIELD(___arg1) == ___arg3') == 2
    assert text.count('___PORT_CHAR_RLO_FIELD(___arg1) == ___arg4') == 2
    assert 'n < 256' in text and '___arg5 < 256' in text
    assert '___VECTORREF(___arg2,___FIX(code)) != ___FAL' in text
    assert '___alloc_scmobj' not in text and 'malloc' not in text
    for guard in ('darwin-gnu-reader-batch', '__APPLE__', '__MACH__', '__GNUC__', '!defined(__clang__)'):
        assert guard in text
