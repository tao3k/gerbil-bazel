(load "patches/gerbil-v19-darwin/tests/syntax-e-native-projection-controls.scm")
(set! calls '())
(dynamic-wind
  (lambda ()
    (set! foldl__0 (lambda (f x marks)
                    (set! calls (cons x calls)) (original-fold f x marks))))
  (lambda ()
    (projection/cdr input)
    (check "cdr retains rebound head and tail effects" (equal? calls '(tail head))))
  (lambda () (set! foldl__0 original-fold)))
(dynamic-wind
  (lambda ()
    (set! foldl__0 (lambda (f x marks)
                    (if (eq? x 'head) (error "head exception")
                      (original-fold f x marks)))))
  (lambda ()
    (check "cdr retains rebound head exception"
      (raises? (lambda () (projection/cdr input)))))
  (lambda () (set! foldl__0 original-fold)))
(define saved-stx-apply gx#stx-apply-mark)
(dynamic-wind
  (lambda () (set! gx#stx-apply-mark (lambda args (apply saved-stx-apply args))))
  (lambda ()
    (check "callback identity guard observes rebinding"
      (not (eq? (##global-var-ref projection-global-6) projection-original-6)))
    (check "rebound callback matches native producer"
      (and (equal? (projection/car input) (car (original-e input)))
           (equal? (projection/cdr input) (cdr (original-e input))))))
  (lambda () (set! gx#stx-apply-mark saved-stx-apply)))
(define saved-inner-fold __foldl1)
(dynamic-wind
  (lambda () (set! __foldl1 (lambda args (apply saved-inner-fold args))))
  (lambda ()
    (check "inner fold identity guard observes rebinding"
      (not (eq? (##global-var-ref projection-global-7) projection-original-7)))
    (check "rebound inner fold matches native producer"
      (and (equal? (projection/car input) (car (original-e input)))
           (equal? (projection/cdr input) (cdr (original-e input))))))
  (lambda () (set! __foldl1 saved-inner-fold)))
(define saved-source gx#stx-source)
(dynamic-wind
  (lambda () (set! gx#stx-source (lambda args (apply saved-source args))))
  (lambda ()
    (check "source identity guard observes rebinding"
      (not (eq? (##global-var-ref projection-global-3) projection-original-3)))
    (check "rebound source matches native producer"
      (and (equal? (projection/car input) (car (original-e input)))
           (equal? (projection/cdr input) (cdr (original-e input))))))
  (lambda () (set! gx#stx-source saved-source)))
(display "OK")
(newline)
