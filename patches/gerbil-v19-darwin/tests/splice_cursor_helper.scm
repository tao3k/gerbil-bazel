;; One pending wrapper, never an unbounded virtual wrapper chain.
(define splice-cursor-platform?
  (c-lambda () bool
#<<splice-cursor-c-end
#if defined(__APPLE__) && defined(__MACH__) && defined(__GNUC__) && !defined(__clang__)
___result = 1;
#else
___result = 0;
#endif
splice-cursor-c-end
))
(define splice-cursor-enabled? (splice-cursor-platform?))
(define splice-cursor-names
  '(gx#syntax-e gx#stx-pair? gx#stx-e gx#stx-apply-mark gx#stx-source
    foldl__0 __foldl1 gx#syntax-wrap::t gx#syntax-quote::t
    gx#identifier-wrap::t gerbil#AST::t))
(define splice-cursor-handles (map ##make-global-var splice-cursor-names))
(define splice-cursor-originals (map ##global-var-ref splice-cursor-handles))
(define splice-cursor-wrap-type gx#syntax-wrap::t)
(define (splice-cursor-canonical?)
  (let loop ((handles splice-cursor-handles) (originals splice-cursor-originals))
    (or (null? handles)
        (and (eq? (##global-var-ref (car handles)) (car originals))
             (loop (cdr handles) (cdr originals))))))
(define (splice-cursor-exact-wrap? value)
  (and (##structure? value)
       (eq? (##structure-type value) splice-cursor-wrap-type)))
(define (splice-cursor-run stx resume)
  (let ((mark (##unchecked-structure-ref stx 3 splice-cursor-wrap-type 'mark)))
    (let loop ((rest (##unchecked-structure-ref stx 1 splice-cursor-wrap-type 'e))
               (heads '()) (initial? #t))
      (if (and (pair? rest) (splice-cursor-canonical?))
          (let* ((head (gx#stx-apply-mark (car rest) mark))
                 (tail (cdr rest))
                 (next-heads (cons head heads)))
            ;; If a callback/interrupt changes bindings, compute the original
            ;; tail fold before resuming, rather than dropping its effects.
            (if (and (not (##structure? tail)) (splice-cursor-canonical?))
                (loop tail next-heads #f)
                (resume (foldl__0
                         (lambda (m value) (gx#stx-apply-mark value m)) tail (list mark))
                        next-heads)))
          (resume (if initial? stx
                      (##structure splice-cursor-wrap-type rest #f mark))
                  heads)))))
