"""Complete buffered ASCII tokens only; retain the original reader on every miss."""
from pathlib import Path


def prepare(text):
    begin = '(define (##build-delimited-string re c i)\n'
    end = '\n(define (##build-delimited-number/keyword/symbol'
    if text.count(begin) != 1 or text.count(end) != 1:
        raise ValueError('exact token reader boundary required')
    start = text.index(begin)
    stop = text.index(end, start)
    original = text[start:stop].rstrip()
    body = original[len(begin):-1]
    replacement = begin + '  (cond-expand\n    (darwin-gnu-reader-batch\n      (or (##gb-darwin-buffered-token re c i)\n' + body + '))\n    (else\n' + body + ')))\n'
    helper = Path(__file__).with_name('darwin_reader_batch_helper.scm').read_text()
    return text[:start] + replacement + text[stop:] + '\n' + helper
