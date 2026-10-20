(if (not (projection-native-platform?)) (error "native projection inactive"))
(define (check name value)
  (if value
    (begin (display "CASE-OK ") (display name) (newline))
    (error "projection control failed" name)))
(define (wrap x mark)
  (##structure gx#syntax-wrap::t x #f mark))
(define inputs
  (list
    (cons 'head 'tail)
    (cons (cons 'nested 'head) 'tail)
    (wrap (cons 'head 'tail) 'a)
    (wrap (wrap (cons 'head 'tail) 'b) 'a)
    (wrap (wrap (cons 'head 'tail) 'a) 'a)
    (wrap (cons (wrap 'head 'a) (wrap 'tail 'b)) 'c)))
(let loop ((rest inputs) (n 0))
  (if (pair? rest)
    (let ((original (gx#syntax-e (car rest))))
      (check (string-append "head equivalence " (number->string n))
        (equal? (car original) (projection/car (car rest))))
      (check (string-append "tail equivalence " (number->string n))
        (equal? (cdr original) (projection/cdr (car rest))))
      (loop (cdr rest) (+ n 1)))))
(define original-fold foldl__0)
(define calls '())
(define input (wrap (cons 'head 'tail) 'a))
(dynamic-wind
  (lambda ()
    (set! foldl__0
      (lambda (f x marks)
        (set! calls (cons x calls))
        (original-fold f x marks))))
  (lambda ()
    (projection/car input)
    (check "rebound fold preserves both effects and order"
      (equal? calls '(tail head))))
  (lambda () (set! foldl__0 original-fold)))
(define (raises? thunk)
  (with-exception-catcher (lambda (exn) #t)
    (lambda () (thunk) #f)))
(dynamic-wind
  (lambda ()
    (set! foldl__0
      (lambda (f x marks)
        (if (eq? x 'tail) (error "tail exception") (original-fold f x marks)))))
  (lambda ()
    (check "tail exception retained"
      (raises? (lambda () (projection/car input)))))
  (lambda () (set! foldl__0 original-fold)))
(define original-e gx#syntax-e)
(dynamic-wind
  (lambda () (set! gx#syntax-e (lambda (x) (cons 'rebound-head 'rebound-tail))))
  (lambda ()
    (check "rebound producer head fallback" (eq? (projection/car input) 'rebound-head))
    (check "rebound producer tail fallback" (eq? (projection/cdr input) 'rebound-tail)))
  (lambda () (set! gx#syntax-e original-e)))
(define original-mark gx#apply-mark)
(dynamic-wind
  (lambda () (set! gx#apply-mark (lambda args (error "not an original inline call"))))
  (lambda ()
    (check "rebound inlined helper selects native producer fallback"
      (equal? (projection/car (wrap input 'b)) (car (original-e (wrap input 'b))))))
  (lambda () (set! gx#apply-mark original-mark)))
(check "mutated bindings restored"
  (and (eq? gx#syntax-e original-e) (eq? foldl__0 original-fold)
       (eq? gx#apply-mark original-mark)))
(display "OK")
(newline)
