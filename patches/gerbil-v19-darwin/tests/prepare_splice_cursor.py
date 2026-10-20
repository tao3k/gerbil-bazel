"""Native Scheme parsing preserves the retained generated module's literals."""
import argparse
import json
import os
from pathlib import Path
import subprocess


PROGRAM = r'''
(define changes 0)
(define (rewrite node)
  (cond
    ((not (pair? node)) node)
    ((eq? (car node) 'quote) node)
    ((and (list? node) (= (length node) 3)
          (eq? (car node) 'define) (eq? (cadr node) 'gx#syntax-split-splice->vector))
     (let* ((old (caddr node)) (args (cadr old)) (stx (car args)) (n (cadr args))
            (lp (caddr old)) (bindings (caddr lp)))
       (if (not (and (= (length old) 3) (eq? (car old) 'lambda)
                     (= (length args) 2) (= (length lp) 4) (eq? (car lp) 'let)
                     (= (length bindings) 2) (equal? (cadar bindings) stx)
                     (equal? (cadadr bindings) '(quote ()))))
           (error "retained splice lambda shape changed"))
       (set! changes (+ changes 1))
       `(define gx#syntax-split-splice->vector
          (lambda ,args
            (let ((splice-resume
                    (lambda (splice-rest splice-heads)
                      (let ,(cadr lp)
                        ((,(caar bindings) splice-rest) (,(caadr bindings) splice-heads))
                        ,(cadddr lp)))))
              (if (and splice-cursor-enabled? (eq? ,n 0)
                       (splice-cursor-canonical?) (splice-cursor-exact-wrap? ,stx)
                       (pair? (##unchecked-structure-ref ,stx 1 splice-cursor-wrap-type 'e)))
                  (splice-cursor-run ,stx splice-resume)
                  (splice-resume ,stx '())))))))
    (else (cons (rewrite (car node)) (rewrite (cdr node))))))
(define forms
  (call-with-input-file INPUT
    (lambda (port)
      (let loop ((forms '()))
        (let ((form (read port)))
          (if (eof-object? form) (reverse forms) (loop (cons form forms))))))))
(define changed (map rewrite forms))
(if (not (= changes 1)) (error "exactly one splice definition required" changes))
(call-with-output-file OUTPUT
  (lambda (port)
    (for-each (lambda (form) (write form port) (newline port)) changed)
    (display HELPER port)))
(display "SPLICE-CURSOR-SOURCE-OK") (newline)
'''


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument('--controls-overlay', action='store_true')
    modes.add_argument('--reference-overlay', action='store_true')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    out = args.output.resolve()
    if not out.is_relative_to(root / '.data') or out.exists():
        parser.error('fresh isolated .data output required')
    home = root / '.data/d1391-runtime-object-source/build'
    source = home / 'lib/static/gerbil__expander__stxcase.scm'
    helper = Path(__file__).with_name('splice_cursor_helper.scm').read_text()
    out.parent.mkdir(parents=True, exist_ok=True)
    program = PROGRAM.replace('INPUT', json.dumps(str(source))).replace(
        'OUTPUT', json.dumps(str(out))).replace('HELPER', json.dumps(helper))
    if args.controls_overlay or args.reference_overlay:
        helper = ('' if args.reference_overlay else
                  '(define splice-cursor-enabled? #t)\n(define splice-cursor-names' + helper.split(
                      '(define splice-cursor-names', 1)[1])
        program = program.replace('(define changed (map rewrite forms))', '''
(define changed '())
(define (select node)
  (if (pair? node)
      (if (and (list? node) (= (length node) 3)
               (eq? (car node) 'define) (eq? (cadr node) 'gx#syntax-split-splice->vector))
          (set! changed (list (rewrite node)))
          (if (not (eq? (car node) 'quote))
              (begin (select (car node)) (select (cdr node)))))))
(for-each select forms)''')
        if args.reference_overlay:
            program = program.replace('(set! changed (list (rewrite node)))',
                                      '(begin (set! changes (+ changes 1)) (set! changed (list node)))')
        program = program.replace(json.dumps(Path(__file__).with_name('splice_cursor_helper.scm').read_text()),
                                  json.dumps(helper))
    env = dict(os.environ, GERBIL_HOME=str(home), GERBIL_LOADPATH=str(home / 'lib'))
    child = subprocess.run([str(root / '.data/d1510-source-loader-linked/gxi'), '-e', program],
                           env=env, capture_output=True, text=True, timeout=20)
    print(child.stdout, end='')
    if child.returncode or child.stderr or child.stdout.splitlines() != ['SPLICE-CURSOR-SOURCE-OK']:
        raise RuntimeError(child.stderr or child.stdout)


if __name__ == '__main__':
    main()
