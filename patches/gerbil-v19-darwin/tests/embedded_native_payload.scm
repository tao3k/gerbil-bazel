(declare (standard-bindings) (extended-bindings))
(set! lazy-control#payload-count (+ lazy-control#payload-count 1))
(set! lazy-control#seen-context lazy-control#context)
(##load lazy-control#dependency-path (lambda args #f) #t #t "lazy_native_dependency" #t)
(define lazy-control#transform
  (lambda (input) (vector (cons input input) lazy-control#seen-context)))
