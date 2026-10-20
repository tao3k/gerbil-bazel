"""Extend the frozen token reader with bounded, unescaped string spans."""
from pathlib import Path

from prepare_darwin_reader_batch import prepare as prepare_tokens


def prepare(text):
    start = text.index('(define (##build-escaped-string-up-to re close)\n')
    end = text.index('\n(define (##build-decimal-integer', start)
    section = text[start:end]
    begin = '          (let loop2 ((c (macro-read-next-char-or-eof re)))'
    finish = '          (make-string i))))'
    if section.count(begin) != 1 or section.count(finish) != 1:
        raise ValueError('exact original escaped string chunk boundary required')
    prefix, rest = section.split(begin)
    body, suffix = rest.split(finish)
    original = (begin + body).rstrip()
    replacement = '''          (cond-expand
            (darwin-gnu-reader-batch
              (let ((span (##gb-darwin-buffered-span re close (- max-chunk-length i))))
                (if span
                    (let* ((n (##string-length span)) (s (loop1 (+ i n))))
                      (##substring-move! span 0 n s i)
                      s)
''' + original + ''')))
            (else
''' + original + '''))
'''
    result = text[:start] + prefix + replacement + finish + suffix + text[end:]
    helper = Path(__file__).with_name('darwin_reader_span_helper.scm').read_text()
    return prepare_tokens(result) + '\n' + helper
