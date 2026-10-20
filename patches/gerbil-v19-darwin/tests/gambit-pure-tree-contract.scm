(declare (standard-bindings) (not safe))

(define (##gb-tree-pick value)
  (if (pair? value) (car value) #f))

(define (##gb-tree-invoke value)
  (##gb-tree-pick value))

(define (##gb-tree-check value)
  (if (not value) (error "pure tree contract failed")))

(define (##gb-tree-run)
  (let ((pair (cons 17 19)))
    (##gb-tree-check (= (##gb-tree-invoke pair) 17))
    (##gb-tree-check (eq? (##gb-tree-invoke 123) #f))
    (set-car! pair 31)
    (##gb-tree-check (= (##gb-tree-invoke pair) 31))
    (##gc)
    (##gb-tree-check (= (##gb-tree-invoke pair) 31))
    (let ((original ##gb-tree-pick))
      (set! ##gb-tree-pick (lambda (value) 41))
      (##gb-tree-check (= (##gb-tree-invoke pair) 41))
      (set! ##gb-tree-pick (lambda (value) (values 7 11)))
      (call-with-values
        (lambda () (##gb-tree-invoke pair))
        (lambda (first second)
          (##gb-tree-check (= first 7))
          (##gb-tree-check (= second 11))))
      (set! ##gb-tree-pick (lambda (value) (error "expected escape")))
      (##gb-tree-check
        (with-exception-catcher
          (lambda (exception) #t)
          (lambda () (##gb-tree-invoke pair) #f)))
      (set! ##gb-tree-pick original))
    (let ((answer
            (call-with-current-continuation
              (lambda (return) (##gc) (return (##gb-tree-invoke pair))))))
      (##gb-tree-check (= answer 31)))
    (let loop ((index 0) (sum 0))
      (if (= index 512)
          (##gb-tree-check (= sum (* 512 31)))
          (loop (+ index 1) (+ sum (##gb-tree-invoke pair))))))
  #t)
