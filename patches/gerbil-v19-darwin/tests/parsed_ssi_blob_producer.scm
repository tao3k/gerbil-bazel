(define (check name value)
  (if value (begin (display "CASE-OK ") (display name) (newline) (force-output))
      (error "parsed SSI serialization control failed" name)))
(define path (getenv "PHI_SSI_PATH"))
(define parsed (##read-all-as-a-begin-expr-from-path path (current-readtable) __wrap-syntax __unwrap-syntax))
(check "reader result and unexpanded syntax" (and (vector? parsed) (AST? (vector-ref parsed 1))))
(define bytes
  (##object->u8vector parsed
    (lambda (object) (if (eq? object AST::t) (##make-global-var 'AST::t) object))))
(check "parsed syntax serialized with canonical type reference" (> (u8vector-length bytes) 0))
(call-with-output-file (getenv "PHI_BLOB_PATH")
  (lambda (port) (write-subu8vector bytes 0 (u8vector-length bytes) port)))
(check "source identity and locations retained" (equal? path (vector-ref parsed 2)))
(display "OK") (newline) (force-output)
