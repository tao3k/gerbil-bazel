;;; Isolated compiler experiment using Gambit's existing primitive expansion API.
(define gb-structure-original-select c#target-select!)
(define gb-structure-expansions 0)
(##add-exit-job!
 (lambda ()
   (display "STRUCTURE-EXPANSIONS ")
   (write gb-structure-expansions)
   (newline)))
(define (gb-structure-install)
  (let* ((prim (c#target.prim-info '##structure-instance-of?))
         (darwin (let ((platform (symbol->string (caddr (system-type)))))
                   (and (>= (string-length platform) 6)
                        (string=? (substring platform 0 6) "darwin")))))
    (if (and darwin prim)
        (begin
          (c#proc-obj-expandable?-set! prim (lambda (env) #t))
          (c#proc-obj-expand-set! prim
            (lambda (ptree oper args generate-call check-binding)
              (if (not (= (length args) 2))
                  #f
                  (let* ((source (c#node-source ptree))
                         (env (c#node-env ptree))
                         (vars (c#gen-temp-vars source args)))
                    (define (ref var) (c#new-ref source env var))
                    (define (call name arguments)
                      (c#gen-call-prim-notsafe source env name arguments))
                    (define (bind expression body)
                      (let ((var (car (c#gen-temp-vars source (list expression)))))
                        (c#new-call source env
                          (c#gen-prc source env (list var) (body var))
                          (list expression))))
                    (define (chain descriptor remaining)
                      (c#new-tst source env
                        (call '##eq? (list (call '##type-id (list (ref descriptor)))
                                         (ref (cadr vars))))
                        (c#new-cst source env #t)
                        (bind (call '##type-super (list (ref descriptor)))
                          (lambda (super)
                            (c#new-tst source env (ref super)
                              (if (= remaining 1)
                                  (generate-call vars #f)
                                  (chain super (- remaining 1)))
                              (c#new-cst source env #f))))))
                    (set! gb-structure-expansions (+ gb-structure-expansions 1))
                    (c#gen-prc source env vars
                      (let ((body
                             (c#new-tst source env
                               (call '##structure? (list (ref (car vars))))
                               (bind (call '##structure-type (list (ref (car vars))))
                                 (lambda (descriptor) (chain descriptor 4)))
                               (c#new-cst source env #f))))
                        (if check-binding
                            (c#new-tst source env (check-binding) body (generate-call vars #f))
                            body)))))))))))
(set! c#target-select!
  (lambda (name options port)
    (gb-structure-original-select name options port)
    (if (eq? name 'C)
        (begin
          (gb-structure-install)
          (display "STRUCTURE-EXPANDER-INSTALLED ")
          (write name)
          (newline)))))
