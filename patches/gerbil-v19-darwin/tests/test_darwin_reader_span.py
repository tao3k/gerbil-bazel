from pathlib import Path
import pytest

from prepare_darwin_reader_span import prepare


ROOT = Path(__file__).resolve().parents[3]


def original():
    return (ROOT / '.data/d1391-runtime-object-source/src/gambit/lib/_io.scm').read_text()


def test_exact_fallback_and_escape_decoder_are_retained():
    text = original()
    result = prepare(text)
    assert '##gb-darwin-buffered-span re close (- max-chunk-length i)' in result
    assert result.count('(let loop2 ((c (macro-read-next-char-or-eof re)))') == 2
    start = text.index('  (define (UCS-4 n)')
    stop = text.index('  (define (read-chunk)', start)
    assert text[start:stop] in result
    assert '(##gb-darwin-buffered-token re c i)' in result


def test_boundary_drift_fails_closed():
    with pytest.raises(ValueError):
        prepare(original().replace('          (make-string i))))', '          (make-string 0))))'))


def test_native_span_is_bounded_locked_and_allocation_free():
    text = Path(__file__).with_name('darwin_reader_span_helper.scm').read_text()
    assert text.count('___PRIMITIVETRYLOCK') == text.count('___PRIMITIVEUNLOCK') == 2
    assert text.count('code >= 128 || code == close || code == 92 || code == 10') == 2
    assert text.count('___PORT_CHAR_RBUF_FIELD(___arg1) == ___arg3') == 2
    assert text.count('___PORT_CHAR_RLO_FIELD(___arg1) == ___arg4') == 2
    assert text.count('___arg5 <= 512') == 2
    assert 'malloc' not in text and '___alloc_scmobj' not in text
