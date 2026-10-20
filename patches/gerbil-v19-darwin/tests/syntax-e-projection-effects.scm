(define (check name value)
  (if value
    (begin (display "CASE-OK ") (display name) (newline))
    (error "projection contract failed" name)))

(define input
  (##structure gx#syntax-wrap::t (cons 'head 'tail) #f 'mark))
(define original-fold foldl__0)
(define original-e gx#syntax-e)
(define (naive-head stx)
  (gx#stx-wrap
    (car (##unchecked-structure-ref stx 1 #f #f))
    (list (##unchecked-structure-ref stx 3 #f #f))))

(define calls 0)
(dynamic-wind
  (lambda ()
    (set! foldl__0
      (lambda (f stx marks)
        (set! calls (+ calls 1))
        (original-fold f stx marks))))
  (lambda ()
    (car (original-e input))
    (check "original projection executes both fields" (= calls 2))
    (set! calls 0)
    (naive-head input)
    (check "naive projection drops observable tail call" (= calls 1)))
  (lambda () (set! foldl__0 original-fold)))

(define (raises? thunk)
  (with-exception-catcher (lambda (exn) #t)
    (lambda () (thunk) #f)))
(dynamic-wind
  (lambda ()
    (set! foldl__0
      (lambda (f stx marks)
        (if (eq? stx 'tail)
          (error "tail effect must remain")
          (original-fold f stx marks)))))
  (lambda ()
    (check "original projection preserves tail exception"
      (raises? (lambda () (car (original-e input)))))
    (check "naive projection wrongly suppresses tail exception"
      (not (raises? (lambda () (naive-head input))))))
  (lambda () (set! foldl__0 original-fold)))
(check "bindings restored" (eq? foldl__0 original-fold))
(display "OK")
(newline)
