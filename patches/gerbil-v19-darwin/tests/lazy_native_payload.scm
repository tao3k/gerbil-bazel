(declare (standard-bindings) (extended-bindings))
(set! lazy-control#payload-count (+ lazy-control#payload-count 1))
(set! lazy-control#seen-context lazy-control#context)
(##load-module 'lazy_native_dependency)
(define lazy-control#transform
  (lambda (input) (vector (cons input input) lazy-control#seen-context)))
