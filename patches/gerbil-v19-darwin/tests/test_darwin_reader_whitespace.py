from pathlib import Path
import pytest

from prepare_darwin_reader_whitespace import ANCHOR, prepare


ROOT = Path(__file__).resolve().parents[3]


def original():
    return (ROOT / '.data/d1391-runtime-object-source/src/gambit/lib/_io.scm').read_text()


def test_original_dispatch_is_retained_and_only_whitespace_handler_changes():
    before = original()
    after = prepare(before)
    assert '##gb-darwin-buffered-whitespace re' in after
    assert '    (else\n     (macro-read-next-char-or-eof re)))' in after
    begin = before.index('(define (##build-escaped-string-up-to re close)')
    end = before.index('(define (##build-decimal-integer', begin)
    assert before[begin:end] in after
    assert '(##gb-darwin-buffered-token re c i)' in after


def test_handler_boundary_drift_rejected():
    with pytest.raises(ValueError):
        prepare(original().replace(ANCHOR, ''))


def test_one_lock_and_no_allocation_or_hardcoded_whitespace_set():
    helper = Path(__file__).with_name('darwin_reader_whitespace_helper.scm').read_text()
    assert helper.count('___PRIMITIVETRYLOCK') == helper.count('___PRIMITIVEUNLOCK') == 1
    assert '___VECTORREF(___arg2,___FIX(code)) != ___arg3' in helper
    assert 'code >= 128' in helper and 'n < 4096' in helper
    assert '___PORT_CHAR_RLINES_FIELD' in helper and '___PORT_CHAR_RCURLINE_FIELD' in helper
    assert 'malloc' not in helper and 'make-string' not in helper
    assert '___SCMOBJ start = ___INT' in helper and '___SCMOBJ end = ___INT' in helper
