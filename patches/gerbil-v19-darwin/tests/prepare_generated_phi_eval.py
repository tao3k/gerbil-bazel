"""Prepare an explicit raw-Scheme artifact branch; never modify the frozen RTS."""
import argparse
import hashlib
import json
from pathlib import Path


ANCHOR = '''            (##eval-module (##vector-ref x 1)
                           (if clone-cte?
                               (##top-cte-clone ##interaction-cte)
                               ##interaction-cte))'''
BRANCH = '''            (if (and (##equal? (##vector-ref x 0)
                                 "gambit-generated-phi-source-v1")
                     ((##c-lambda () bool
                        "#if defined(__APPLE__) && defined(__MACH__) && defined(__GNUC__) && !defined(__clang__)\\n___result = 1;\\n#else\\n___result = 0;\\n#endif")))
                (let ((top-cte (if clone-cte?
                                  (##top-cte-clone ##interaction-cte)
                                  ##interaction-cte)))
                  ;; Keep the compiler context, demanded modules and location conversion.
                  ;; Only this explicitly tagged artifact bypasses the language expander.
                  (##setup-requirements-and-run
                   (##call-with-values
                    (lambda ()
                      (##in-new-compilation-ctx
                       (macro-interpreter-target)
                       (lambda () (##comp-top top-cte (##vector-ref x 1) #f))))
                    (lambda (code ctx)
                      (##extract-demand-modules (##convert-source-to-locat! code) ctx)))
                   #f))
''' + ANCHOR.strip() + ')'


COMPILED_ANCHOR = '''    (macro-psettings-path-set! psettings source-path)
    (let ((x'''
COMPILED_PREFIX = '''    (macro-psettings-path-set! psettings source-path)
    (let ((compiled
           (and (##string? path-or-settings)
                ((##c-lambda () bool
                   "#if defined(__APPLE__) && defined(__MACH__) && defined(__GNUC__) && !defined(__clang__)\\n___result = 1;\\n#else\\n___result = 0;\\n#endif"))
                (##call-with-input-file
                 (##list 'path: source-path 'char-encoding: 'ISO-8859-1 'eol-encoding: 'lf)
                 (lambda (port)
                   (let ((header (##make-u8vector 25 0)))
                     (and (##fx= (read-subu8vector header 0 25 port 25) 25)
                          (##equal? header '#u8(35 33 103 97 109 98 105 116 45 99 111 109 112 105 108 101 100 45 112 104 105 45 118 49 10))
                          (let* ((size (##fx- (file-info-size (file-info source-path))
                                            25))
                                 (bytes (if (and (##fx> size 0) (##fx< size 134217728))
                                            (##make-u8vector size 0)
                                            (##error "invalid compiled phi artifact size" source-path))))
                            (if (##not (##fx= (read-subu8vector bytes 0 size port size) size))
                                (##error "truncated compiled phi artifact" source-path))
                            (##u8vector->object bytes)))))))))
      (if compiled
          (begin
            (script-callback "gambit-compiled-phi-v1" source-path)
            (##setup-requirements-and-run compiled #f)
            source-path)
    (let ((x'''


def prepare(text, compiled=False):
    if text.count(ANCHOR) != 1:
        raise ValueError('exact original load-source boundary required')
    text = text.replace(ANCHOR, BRANCH, 1)
    if compiled:
        if text.count(COMPILED_ANCHOR) != 1:
            raise ValueError('exact original source port boundary required')
        text = text.replace(COMPILED_ANCHOR, COMPILED_PREFIX, 1)
        end = '            (##vector-ref x 2)))))\n\n  (define (load-binary'
        if text.count(end) != 1:
            raise ValueError('exact source load result boundary required')
        text = text.replace(end, '            (##vector-ref x 2)))))))\n\n  (define (load-binary', 1)
    return text


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    out = args.output.resolve()
    if not out.is_relative_to(root / '.data') or out.exists():
        parser.error('fresh isolated .data source required')
    original = root / '.data/d1391-runtime-object-source/src/gambit/lib/_eval.scm'
    data = original.read_bytes()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(prepare(data.decode()))
    print(json.dumps(dict(originalSha256=hashlib.sha256(data).hexdigest(),
                          preparedSha256=hashlib.sha256(out.read_bytes()).hexdigest())))


if __name__ == '__main__':
    main()
