(declare (standard-bindings) (extended-bindings))
(define lazy-control#payload-count 0)
(define lazy-control#dependency-count 0)
(define lazy-control#context #f)
(define lazy-control#seen-context #f)
(define (check name value)
  (if value
      (begin (display "CASE-OK ") (display name) (newline) (force-output))
      (error "lazy native contract failed" name)))
(check "payload registered before import"
  (and (##lookup-registered-module 'lazy_native_payload) #t))
(check "dependency registered before import"
  (and (##lookup-registered-module 'lazy_native_dependency) #t))
(check "payload initializer is deferred" (= lazy-control#payload-count 0))
(check "dependency initializer is deferred" (= lazy-control#dependency-count 0))
(define context (list 'fresh 'macro-context))
(set! lazy-control#context context)
(##load-module 'lazy_native_payload)
(check "payload initializer runs on import" (= lazy-control#payload-count 1))
(check "nested dependency initializes on demand" (= lazy-control#dependency-count 1))
(check "initializer retains actual import context" (eq? lazy-control#seen-context context))
(define input (list 'shared 'input))
(define result (lazy-control#transform input))
(check "native transformer retains aliases"
  (and (eq? (car (vector-ref result 0)) input)
       (eq? (cdr (vector-ref result 0)) input)))
(check "native transformer creates fresh output"
  (not (eq? result (lazy-control#transform input))))
(##load-module 'lazy_native_payload)
(check "repeat import does not repeat initializer" (= lazy-control#payload-count 1))
(check "repeat import does not repeat dependency" (= lazy-control#dependency-count 1))
(check "initializer exceptions propagate"
  (with-exception-catcher
    (lambda (exception) #t)
    (lambda () (##load-module 'lazy_native_failure) #f)))
(##gc)
(check "live native outputs survive collection"
  (and (eq? (vector-ref result 1) context)
       (eq? (car (vector-ref result 0)) input)))
(display "OK") (newline) (force-output)
