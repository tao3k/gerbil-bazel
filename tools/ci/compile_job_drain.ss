;;; A compiler error is observable only after peer and nested jobs quiesce.
(import :gerbil/compiler/base)
(def peer-complete? #f)
(def nested-complete? #f)
(def caught-false? #f)
(add-compile-job! (lambda () (raise #f)) 'failed-producer)
(add-compile-job!
 (lambda ()
   (thread-sleep! .1)
   (set! peer-complete? #t)
   (add-compile-job! (lambda () (set! nested-complete? #t)) 'nested-peer))
 'delayed-peer)
(with-catch
 (lambda (failure) (set! caught-false? (eq? failure #f)))
 (lambda () (execute-pending-compile-jobs!)))
(unless (and caught-false? peer-complete? nested-complete?)
 (error "compiler returned before failure peers and follow-ups drained"
        caught-false? peer-complete? nested-complete?))
(def recovered? #f)
(add-compile-job! (lambda () (set! recovered? #t)) 'recovery)
(execute-pending-compile-jobs!)
(unless recovered? (error "compiler failure poisoned next build"))
(displayln "COMPILE-JOB-DRAIN-OK false failure, peers, follow-ups, recovery")
