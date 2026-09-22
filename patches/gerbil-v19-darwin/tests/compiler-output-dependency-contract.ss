;;; Atomic contract for candidate Patch 0007 output dependencies.
;;; This is not part of the four-patch release gate.
(import :gerbil/compiler/base)

(def first-ran? #f)
(def late-ran? #f)
(add-compile-output-job! 'ready (lambda () (void)) 'produce-ready)
(add-compile-dependent-job!
 ['ready]
 (lambda ()
   (set! first-ran? #t)
   ;; This subscription is deterministically after output publication.
   (add-compile-dependent-job!
    ['ready] (lambda () (set! late-ran? #t)) 'late-dependent))
 'first-dependent)
(execute-pending-compile-jobs!)
(unless (and first-ran? late-ran?)
  (error "completed output did not release early and late dependents"))

(def left-ran? #f)
(def right-ran? #f)
(def both-ran? #f)
(add-compile-output-job! 'left (lambda () (set! left-ran? #t)) 'produce-left)
(add-compile-output-job! 'right (lambda () (set! right-ran? #t)) 'produce-right)
(add-compile-dependent-job!
 ['left 'right]
 (lambda ()
   (unless (and left-ran? right-ran?)
     (error "dependent started before both outputs completed"))
   (set! both-ran? #t))
 'after-both)
(execute-pending-compile-jobs!)
(unless both-ran?
  (error "two-output dependency was not released"))

(def duplicate-rejected? #f)
(add-compile-output-job! 'duplicate (lambda () (void)) 'first-producer)
(with-catch
 (lambda (error) (set! duplicate-rejected? #t))
 (lambda ()
   (add-compile-output-job! 'duplicate (lambda () (void)) 'second-producer)))
(execute-pending-compile-jobs!)
(unless duplicate-rejected?
  (error "duplicate output producer was accepted"))

(def unknown-rejected? #f)
(with-catch
 (lambda (error) (set! unknown-rejected? #t))
 (lambda ()
   (add-compile-dependent-job!
    ['unregistered] (lambda () (void)) 'unknown-dependent)))
(execute-pending-compile-jobs!)
(unless unknown-rejected?
  (error "unregistered output dependency was accepted"))

;; #f is a valid raised object. A dependent must not run after this failure.
(def false-failure-caught? #f)
(def false-failure-dependent-ran? #f)
(add-compile-output-job! 'raises-false (lambda () (raise #f)) 'false-producer)
(add-compile-dependent-job!
 ['raises-false]
 (lambda () (set! false-failure-dependent-ran? #t))
 'false-dependent)
(with-catch
 (lambda (error) (set! false-failure-caught? (eq? error #f)))
 (lambda () (execute-pending-compile-jobs!)))
(unless false-failure-caught?
  (error "output producer did not propagate its #f failure"))
(when false-failure-dependent-ran?
  (error "dependent ran after output producer raised #f"))

(displayln "compiler output dependency contract passed")
