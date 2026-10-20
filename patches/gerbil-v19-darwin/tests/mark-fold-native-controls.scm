(if (not mark-fold-native-enabled?) (error "mark fold candidate inactive"))
(define (check name value)
  (if value (begin (display "CASE-OK ") (display name) (newline))
    (error "mark fold semantic control failed" name)))
(define saved-fold foldl__0)
(define saved-inner __foldl1)
(define saved-apply gx#stx-apply-mark)
(define saved-source gx#stx-source)
(define saved-type gx#syntax-wrap::t)
(define (reference value marks)
  (saved-fold (lambda (mark rest) (saved-apply rest mark)) value marks))
(define values-to-check
  (list 'head (cons 'head 'tail) '#(head tail) "head"
        (##structure saved-type 'head 'origin 'a)
        (##structure saved-type (cons 'head 'tail) #f 'b)))
(define marks-to-check (list '() '(a) '(a b) '(a a) '(a b a) '(a . b)))
(let outer ((values values-to-check) (i 0))
  (if (pair? values)
    (begin
      (let inner ((marks marks-to-check) (j 0))
        (if (pair? marks)
          (let* ((value (car values)) (expected (reference value (car marks)))
                 (actual (gx#stx-wrap value (car marks))))
            (check (string-append "value and alias " (number->string i) ":" (number->string j))
              (and (equal? actual expected) (if (eq? expected value) (eq? actual value) #t)))
            (inner (cdr marks) (+ j 1)))))
      (outer (cdr values) (+ i 1)))))
(define count 0)
(dynamic-wind
  (lambda () (set! foldl__0 (lambda args (set! count (+ count 1)) (apply saved-fold args))))
  (lambda ()
    (check "fold identity guard observes rebinding"
      (not (eq? (##global-var-ref mark-fold-global-0) mark-fold-original-0)))
    (gx#stx-wrap 'head '(a b))
    (check "rebound fold execution retained" (= count 1)))
  (lambda () (set! foldl__0 saved-fold)))
(dynamic-wind
  (lambda () (set! foldl__0 (lambda args (error "rebound fold"))))
  (lambda ()
    (check "rebound fold exception retained"
      (with-exception-catcher (lambda (error) #t)
        (lambda () (gx#stx-wrap 'head '(a)) #f))))
  (lambda () (set! foldl__0 saved-fold)))
(dynamic-wind
  (lambda () (set! __foldl1 (lambda args (apply saved-inner args))))
  (lambda ()
    (check "inner identity guard observes rebinding"
      (not (eq? (##global-var-ref mark-fold-global-1) mark-fold-original-1)))
    (check "rebound inner fold native result retained"
      (equal? (gx#stx-wrap 'head '(a b)) (reference 'head '(a b)))))
  (lambda () (set! __foldl1 saved-inner)))
(dynamic-wind
  (lambda () (set! gx#stx-apply-mark (lambda args (apply saved-apply args))))
  (lambda ()
    (check "callback identity guard observes rebinding"
      (not (eq? (##global-var-ref mark-fold-global-2) mark-fold-original-2)))
    (check "rebound callback native result retained"
      (equal? (gx#stx-wrap 'head '(a b)) (reference 'head '(a b)))))
  (lambda () (set! gx#stx-apply-mark saved-apply)))
(dynamic-wind
  (lambda () (set! gx#stx-source (lambda args (apply saved-source args))))
  (lambda ()
    (check "source identity guard observes rebinding"
      (not (eq? (##global-var-ref mark-fold-global-3) mark-fold-original-3)))
    (check "rebound source native result retained"
      (equal? (gx#stx-wrap 'head '(a b)) (reference 'head '(a b)))))
  (lambda () (set! gx#stx-source saved-source)))
(dynamic-wind
  (lambda () (set! gx#syntax-wrap::t gx#identifier-wrap::t))
  (lambda ()
    (check "constructor identity guard observes rebinding"
      (not (eq? (##global-var-ref mark-fold-global-4) mark-fold-original-4)))
    (check "rebound constructor native result retained"
      (equal? (gx#stx-wrap 'head '(a)) (reference 'head '(a)))))
  (lambda () (set! gx#syntax-wrap::t saved-type)))
(check "all native bindings restored"
  (and (eq? foldl__0 saved-fold) (eq? __foldl1 saved-inner)
       (eq? gx#stx-apply-mark saved-apply) (eq? gx#stx-source saved-source)
       (eq? gx#syntax-wrap::t saved-type)))
(display "OK") (newline)
