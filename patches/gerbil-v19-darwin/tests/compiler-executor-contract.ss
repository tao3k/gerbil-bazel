;;; Atomic contract for the Darwin streaming compiler executor.
;;; Run in a fresh gxi process for each GERBIL_BUILD_CORES value.
(import :gerbil/compiler/base)

(def submitted-context #f)
(parameterize ((current-compile-context 'submitted))
  (add-compile-job!
   (lambda ()
     (set! submitted-context (current-compile-context)))
   'capture-context))
(execute-pending-compile-jobs!)
(unless (eq? submitted-context 'submitted)
  (error "compiler executor lost submission parameterization"))

(def nested-completed? #f)
(add-compile-job!
 (lambda ()
   (add-compile-job!
    (lambda () (set! nested-completed? #t))
    'nested-job))
 'submit-nested-job)
(execute-pending-compile-jobs!)
(unless nested-completed?
  (error "compiler executor failed to drain nested work"))

;; #f is a valid raised object, not a success sentinel.
(def caught-false-error? #f)
(add-compile-job! (lambda () (raise #f)) 'raise-false)
(with-catch
 (lambda (error)
   (set! caught-false-error? (eq? error #f)))
 (lambda () (execute-pending-compile-jobs!)))
(unless caught-false-error?
  (error "compiler executor swallowed a #f exception"))

;; A failed batch must not poison the following build session.
(def recovered? #f)
(add-compile-job! (lambda () (set! recovered? #t)) 'recover)
(execute-pending-compile-jobs!)
(unless recovered?
  (error "compiler executor did not reopen after failure"))

(displayln "compiler executor contract passed")
