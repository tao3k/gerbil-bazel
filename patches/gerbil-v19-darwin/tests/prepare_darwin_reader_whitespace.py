"""Skip only actual buffered whitespace handlers, without a string allocation."""
from pathlib import Path

from prepare_darwin_reader_batch import prepare as prepare_tokens


ANCHOR = '''(define (##read-whitespace re c)
  (macro-read-next-char-or-eof re) ;; skip whitespace character
  (##read-datum-or-label-or-none-or-dot re)) ;; read what follows whitespace'''
REPLACEMENT = '''(define (##read-whitespace re c)
  (cond-expand
    (darwin-gnu-reader-batch
     (if (##fx= (##gb-darwin-buffered-whitespace re) 0)
         (macro-read-next-char-or-eof re)))
    (else
     (macro-read-next-char-or-eof re)))
  (##read-datum-or-label-or-none-or-dot re)) ;; read what follows whitespace'''


def prepare(text):
    if text.count(ANCHOR) != 1:
        raise ValueError('exact original whitespace dispatch boundary required')
    helper = Path(__file__).with_name('darwin_reader_whitespace_helper.scm').read_text()
    return prepare_tokens(text.replace(ANCHOR, REPLACEMENT, 1)) + '\n' + helper
