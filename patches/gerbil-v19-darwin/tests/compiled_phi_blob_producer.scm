(define (check name value)
  (if value (begin (display "CASE-OK ") (display name) (newline) (force-output))
      (error "compiled phi serialization control failed" name)))
(define body
  '(begin
     (define phi-blob#state (vector 0))
     (define phi-blob#bump
       (lambda () (vector-set! phi-blob#state 0 (+ 1 (vector-ref phi-blob#state 0)))
                  (vector-ref phi-blob#state 0)))
     (define phi-blob#alias (lambda (x) (vector x x)))
     (define phi-blob#values (lambda () (values 'first 'second)))
     (define phi-blob#failure (lambda () (error "retained failure")))))
(define top-cte (##top-cte-clone ##interaction-cte))
(define compiled
  (##call-with-values
    (lambda ()
      (##in-new-compilation-ctx '(c)
        (lambda () (##comp-top top-cte (##sourcify body (##make-source #f #f)) #f))))
    (lambda (code ctx)
      (##extract-demand-modules (##convert-source-to-locat! code) ctx))))
(check "compiled module has code and demand list" (pair? compiled))
(define bytes (##object->u8vector compiled))
(check "compiled module serialized" (> (u8vector-length bytes) 0))
(call-with-output-file (getenv "PHI_BLOB_PATH")
  (lambda (port) (write-subu8vector bytes 0 (u8vector-length bytes) port)))
(check "producer does not execute module" (##unbound? (##global-var-ref (##make-global-var 'phi-blob#state))))
(display "OK") (newline) (force-output)
