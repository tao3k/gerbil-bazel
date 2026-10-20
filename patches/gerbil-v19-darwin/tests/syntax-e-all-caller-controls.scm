(define (check name value)
  (if value (begin (display "CASE-OK ") (display name) (newline))
    (error "caller transformation failed" name)))
(define (rewrite form) (projection-transform-all (list form)))
(define (count-changes result) (length (cdr result)))
(check "direct car" (= 1 (count-changes (rewrite '(##car (gx#syntax-e x))))))
(check "direct cdr" (= 1 (count-changes (rewrite '(##cdr (gx#syntax-e x))))))
(check "single let return"
  (= 1 (count-changes (rewrite '(let ((p (gx#syntax-e x))) (##car p))))))
(check "unused tail binding"
  (= 1 (count-changes
    (rewrite '(let ((p (gx#syntax-e x)))
                (let ((h (##car p)) (t (##cdr p))) h))))))
(check "unused head binding"
  (= 1 (count-changes
    (rewrite '(let ((p (gx#syntax-e x)))
                (let ((h (##car p)) (t (##cdr p))) t))))))
(check "both fields used unchanged"
  (= 0 (count-changes
    (rewrite '(let ((p (gx#syntax-e x)))
                (let ((h (##car p)) (t (##cdr p))) (cons h t)))))))
(check "pair escapes unchanged"
  (= 0 (count-changes
    (rewrite '(let ((p (gx#syntax-e x)))
                (let ((h (##car p)) (t (##cdr p))) (cons p h)))))))
(check "quoted program unchanged"
  (= 0 (count-changes (rewrite '(quote (##car (gx#syntax-e x)))))))
(let* ((form '(define sample (lambda (x) (cons #\# (##car (gx#syntax-e x))))))
       (result (rewrite form)))
  (check "native character datum preserved" (equal? (cadr (caddr (caddr (caar result)))) '#\#))
  (check "definition owner recorded" (eq? (caadr result) 'sample)))
(display "OK")
(newline)
