;;; Real worker-pool metadata controls; no C compilation or timing claim.
(import :gerbil/compiler/base)

(def enabled? (equal? (getenv "GAMBIT_DARWIN_CLOSED_LINK_RECIPE_PROOF" #f) "1"))
(def recipe-called? #f)
(def producer-options [(string-copy "-O2")])
(def success-ran? #f)
(def executor (current-or-open-compile-executor))
(parameterize ((current-compile-gsc-options producer-options))
  (add-compile-output-job! 'successful
    (lambda ()
      (when (current-compile-output-recipe 'successful)
        (error "pending producer exposed recipe"))
      ;; Mutating the producer's option string must not mutate its snapshot.
      (string-set! (car producer-options) 2 #\3))
    'successful-producer
    (lambda ()
      (set! recipe-called? #t)
      (unless (equal? (current-compile-gsc-options) ["-O2"])
        (error "worker lost submitted compiler parameterization"))
      (current-compile-gsc-options))))
(add-compile-dependent-job! ['successful]
  (lambda ()
    (let (recipe (current-compile-output-recipe 'successful))
      (if enabled?
        (begin
          (unless (equal? recipe ["-O2"])
            (error "published recipe did not retain producer options" recipe))
          (string-set! (car recipe) 2 #\9)
          (unless (equal? (current-compile-output-recipe 'successful) ["-O2"])
            (error "reader mutated published recipe")))
        (when recipe (error "disabled executor published recipe"))))
    (set! success-ran? #t))
  'successful-consumer)
(execute-pending-compile-jobs!)
(unless (and success-ran? (eq? enabled? recipe-called?))
  (error "recipe opt-in callback contract failed"))
(unless (equal? ((compile-executor-output-produced? executor) 'successful #t)
                (and enabled? ["-O2"]))
  (error "closed executor lost successful recipe"))

;; Both outputs must be complete before a dependent can observe their recipes.
(def both-ran? #f)
(def barrier-mx (make-mutex 'recipe-contract-barrier))
(def barrier-cv (make-condition-variable 'recipe-contract-barrier))
(def arrived 0)
(def (concurrent-producer)
  (mutex-lock! barrier-mx)
  (set! arrived (+ arrived 1))
  (condition-variable-broadcast! barrier-cv)
  (let wait ()
    (unless (= arrived 2)
      (mutex-unlock! barrier-mx barrier-cv)
      (mutex-lock! barrier-mx)
      (wait)))
  (mutex-unlock! barrier-mx))
(for-each
  (lambda (output)
    (add-compile-output-job! output concurrent-producer output
      (lambda () [(symbol->string output)])))
  ['left 'right])
(add-compile-dependent-job! ['left 'right]
  (lambda ()
    (for-each
      (lambda (output)
        (unless (equal? (current-compile-output-recipe output)
                        (and enabled? [(symbol->string output)]))
          (error "multi-output dependent saw incomplete recipe" output)))
      ['left 'right])
    (set! both-ran? #t))
  'both-consumer)
(execute-pending-compile-jobs!)
(unless both-ran? (error "multi-output dependent was not released"))

(def (check-failed-producer output fail-in-recipe?)
  (def executor (current-or-open-compile-executor))
  (def caught? #f)
  (def dependent-ran? #f)
  (add-compile-output-job! output
    (lambda () (raise #f)) output
    (lambda () (if fail-in-recipe? (raise #f) ["-O2"])))
  (add-compile-dependent-job! [output]
    (lambda () (set! dependent-ran? #t)) 'failed-consumer)
  (with-catch
    (lambda (exception) (set! caught? (eq? exception #f)))
    (lambda () (execute-pending-compile-jobs!)))
  (unless (and caught? (not dependent-ran?)
               (not ((compile-executor-output-produced? executor) output #t)))
    (error "failed producer exposed recipe or released dependent" output)))
(check-failed-producer 'failed-output #f)
(check-failed-producer 'failed-recipe #t)
(displayln "PRODUCER-RECIPE-LIFECYCLE-OK enabled=" enabled?)
