;; Generic Gerbil binding semantics, not a timing or package fixture.
(def checks 0)
(def (check name actual expected)
  (unless (equal? actual expected)
    (error "parameter binding contract" name actual expected))
  (set! checks (+ checks 1))
  (displayln "PARAMETER-BINDING-CASE-OK " name))

(def p (make-parameter 1))
(def q (make-parameter 2))
(check 'later-value-sees-earlier-binding
  (parameterize ((p 10) (q (p))) (list (p) (q))) '(10 10))
(check 'original-scope-restored (list (p) (q)) '(1 2))

(def filter-seen #f)
(def filtered
  (make-parameter 0 (lambda (value) (set! filter-seen (p)) value)))
(set! filter-seen #f)
(check 'later-filter-sees-earlier-binding
  (parameterize ((p 20) (filtered 30))
    (list (p) (filtered) filter-seen)) '(20 30 20))
(check 'filtered-scope-restored (list (p) (filtered)) '(1 0))

(check 'duplicate-parameter-value
  (parameterize ((p 10) (p (+ (p) 1))) (p)) 11)
(check 'duplicate-scope-restored (p) 1)

(def custom-value 1)
(def custom-sets [])
(def (custom . args)
  (if (null? args) custom-value
    (begin
      (set! custom-value (car args))
      (set! custom-sets (cons custom-value custom-sets)))))
(check 'custom-procedure-binding (parameterize ((custom 77)) (custom)) 77)
(check 'custom-procedure-restoration (list custom-value (reverse custom-sets)) '(1 (77 1)))

(check 'nonlocal-escape
  (call/cc (lambda (escape) (parameterize ((p 42)) (escape (p))))) 42)
(check 'escape-restoration (p) 1)
(check 'exception
  (with-catch (lambda (_) 'caught)
    (lambda () (parameterize ((p 43)) (error "expected contract exception")))) 'caught)
(check 'exception-restoration (p) 1)

(check 'multiple-values
  (call-with-values
    (lambda () (parameterize ((p 7) (q 8)) (values (p) (q)))) list) '(7 8))

(check 'thread-inheritance
  (parameterize ((p 90))
    (let (child (make-thread (lambda () (thread-yield!) (p))))
      (thread-start! child)
      (thread-join! child))) 90)
(check 'thread-parent-restoration (p) 1)

(let ((resume #f) (resumed? #f) (inside []) (outside []))
  (parameterize ((p 80))
    (call/cc (lambda (k) (set! resume k)))
    (set! inside (cons (p) inside)))
  (set! outside (cons (p) outside))
  (if resumed?
    (check 'continuation-reentry (list inside outside) '((80 80) (1 1)))
    (begin (set! resumed? #t) (resume 'again))))

(check 'equal-value-binding-is-mutable
  (parameterize ((p (p))) (p 77) (p)) 77)
(check 'equal-value-binding-does-not-alias-parent (p) 1)
(check 'nested-equal-value-binding-isolation
  (parameterize ((p 10))
    (list (parameterize ((p (p))) (p 99) (p)) (p))) '(99 10))
(check 'nested-equal-value-parent-restored (p) 1)

(check 'final-original-scope (list (p) (q)) '(1 2))
(displayln "PARAMETER-BINDING-OK " checks)
