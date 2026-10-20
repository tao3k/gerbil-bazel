(define (check name value)
  (if value (begin (display "CASE-OK ") (display name) (newline) (force-output))
      (error "parsed SSI deserialization control failed" name)))
(define path (getenv "PHI_BLOB_PATH"))
(define source-path (getenv "PHI_SSI_PATH"))
(define bytes (make-u8vector (file-info-size (file-info path))))
(call-with-input-file path
  (lambda (port)
    (check "whole parsed syntax artifact read"
      (= (read-subu8vector bytes 0 (u8vector-length bytes) port (u8vector-length bytes))
         (u8vector-length bytes)))))
(define (restore)
  (##u8vector->object bytes
    (lambda (object) (if (##global-var? object) (##global-var-ref object) object))))
(define restored (restore))
(check "reader tuple restored in fresh process" (and (vector? restored) (= (vector-length restored) 3)))
(check "AST predicate and canonical structure descriptor"
  (and (AST? (vector-ref restored 1)) (eq? (##structure-type (vector-ref restored 1)) AST::t)))
(define reference
  (##read-all-as-a-begin-expr-from-path source-path (current-readtable) __wrap-syntax __unwrap-syntax))
(check "all unexpanded datum equals original reader"
  (equal? (__AST->datum (vector-ref reference 1)) (__AST->datum (vector-ref restored 1))))
(check "file and source locations retained"
  (and (equal? (vector-ref reference 2) (vector-ref restored 2))
       (equal? (AST-source (vector-ref reference 1)) (AST-source (vector-ref restored 1)))))
(define second (restore))
(define first-node (cadr (AST-e (vector-ref restored 1))))
(AST-e-set! first-node 'mutated-control)
(check "fresh mutable syntax tree for every restore"
  (equal? (__AST->datum (vector-ref reference 1)) (__AST->datum (vector-ref second 1))))
(check "mutation cannot leak to another restored tree"
  (not (eq? first-node (cadr (AST-e (vector-ref second 1))))))
(##gc)
(check "restored syntax and canonical type survive GC"
  (and (AST? (vector-ref second 1))
       (equal? (__AST->datum (vector-ref reference 1)) (__AST->datum (vector-ref second 1)))))
(display "OK") (newline) (force-output)
