(define case-count 0)
(define (check name value)
  (unless value (error "native stage contract failed" name))
  (set! case-count (+ case-count 1))
  (display "IMPORT-BINDING-CASE\t") (write name) (newline))
(define module-path (getenv "NATIVE_STAGE_MODULE"))
(define marker-path (getenv "NATIVE_STAGE_MARKER"))
(define (marker)
  (and (file-exists? marker-path)
       (call-with-input-file marker-path
         (lambda (port) (read-line port #f)))))
(define slot (##make-global-var 'd1510-native-stage-value))
(define before (list (##global-var-ref slot)))
(when (equal? (getenv "NATIVE_STAGE_GERBIL_LOAD" #f) "1")
  (set-load-path! (cons (path-directory module-path) (load-path)))
  (let* ((name "native_stage_module")
         (first-error
          (with-exception-catcher (lambda (exn) (list exn))
            (lambda () (load-module name) #f))))
    (check 'gerbil-loader-first-error-propagates
      (and (pair? first-error) (eq? (car first-error) 'native-stage-failure)))
    (check 'gerbil-loader-effects-in-original-order (equal? (marker) "C\nSCHEME\n"))
    (let ((state (hash-get __modules name)))
      (check 'gerbil-loader-caches-exact-error
        (and (pair? state) (eq? (car state) 'error) (eq? (cadr state) (car first-error)))))
    (check 'gerbil-loader-retains-uninitialized-value (##unbound? (##global-var-ref slot)))
    (check 'gerbil-loader-second-error-identical
      (with-exception-catcher (lambda (exn) (eq? exn (car first-error)))
        (lambda () (load-module name) #f)))
    (check 'gerbil-loader-replay-does-not-repeat-effects (equal? (marker) "C\nSCHEME\n")))
  (display "IMPORT-BINDING-OK\t") (write case-count) (newline)
  (exit 0))
(define descriptor-result
  (##load-object-file module-path (path-strip-directory module-path) #t))
(check 'native-descriptors-returned
  (and (vector? descriptor-result) (= (vector-length descriptor-result) 3)
       (= (vector-length (vector-ref descriptor-result 0)) 1)))
(check 'mapping-defers-c-and-scheme (not (marker)))
(define mapped-state (list (##global-var-ref slot)))
(check 'mapping-records-supplied-but-uninitialized-global
  (and (##unbound? (car before)) (##unbound? (car mapped-state))
       (not (eq? (car before) (car mapped-state)))))
(define descriptors (vector-ref descriptor-result 0))
(##gc)
(check 'descriptor-thunk-survives-gc
  (procedure? (vector-ref (vector-ref descriptors 0) 4)))
(##register-module-descrs descriptors)
(define modules
  (map (lambda (md)
         (##lookup-registered-module (##vector-last (vector-ref md 0))))
       (vector->list descriptors)))
(##init-modules modules 0)
(check 'zero-stage-preserves-effects (not (marker)))
(##init-modules modules 1)
(check 'stage-one-only-c (equal? (marker) "C\n"))
(check 'stage-one-preserves-scheme-value (eq? (car mapped-state) (##global-var-ref slot)))
(if (equal? (getenv "NATIVE_STAGE_THROW" #f) "1")
  (begin
    (check 'failing-stage-two-propagates-exact-error
      (with-exception-catcher (lambda (exn) (eq? exn 'native-stage-failure))
        (lambda () (##init-modules modules 2) #f)))
    (check 'failing-stage-two-records-started-stage
      (= (vector-ref (car modules) 1) 2))
    (check 'failing-stage-two-preserves-uninitialized-value
      (eq? (car mapped-state) (##global-var-ref slot)))
    (check 'failing-stage-two-retains-prior-effects (equal? (marker) "C\nSCHEME\n"))
    (check 'repeated-failed-init-does-not-replay-error-or-thunk
      (and (with-exception-catcher (lambda (exn) #f)
             (lambda () (##init-modules modules 2) #t))
           (eq? (car mapped-state) (##global-var-ref slot))
           (equal? (marker) "C\nSCHEME\n"))))
  (begin
    (##init-modules modules 2)
    (let ((value (##global-var-ref slot)))
      (check 'stage-two-orders-c-before-scheme (equal? (marker) "C\nSCHEME\n"))
      (check 'stage-two-sets-live-value (equal? value '(native-stage-value)))
      (##init-modules modules 2)
      (check 'repeated-init-preserves-identity-and-effects
        (and (eq? value (##global-var-ref slot)) (equal? (marker) "C\nSCHEME\n"))))))
(check 'duplicate-native-map-is-refused
  (fixnum? (##load-object-file module-path (path-strip-directory module-path) #t)))
(display "IMPORT-BINDING-OK\t") (write case-count) (newline)
