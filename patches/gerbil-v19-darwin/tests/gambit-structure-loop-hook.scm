;;; Isolated loop expansion using the same recursive IR pattern as memq.
(define gb-structure-original-select c#target-select!)
(define gb-structure-expansions 0)
(##add-exit-job!
 (lambda ()
   (display "STRUCTURE-EXPANSIONS ")
   (write gb-structure-expansions)
   (newline)))
(define (gb-structure-install)
  (let* ((prim (c#target.prim-info '##structure-instance-of?))
         (platform (symbol->string (caddr (system-type)))))
    (if (and prim (>= (string-length platform) 6)
             (string=? (substring platform 0 6) "darwin"))
        (begin
          (c#proc-obj-expandable?-set! prim (lambda (env) #t))
          (c#proc-obj-expand-set! prim
            (lambda (ptree oper args generate-call check-binding)
              (if (not (= (length args) 2))
                  #f
                  (let* ((source (c#node-source ptree))
                         (env (c#node-env ptree))
                         (tail-env (c#add-proper-tail-calls env))
                         (vars (c#gen-temp-vars source args))
                         (loop-var (c#new-temp-variable source 'type-loop))
                         (descriptor (c#new-temp-variable source 'descriptor))
                         (super (c#new-temp-variable source 'super)))
                    (define (ref var) (c#new-ref source env var))
                    (define (call name arguments)
                      (c#gen-call-prim-notsafe source env name arguments))
                    (define (gen-loop)
                      (c#new-call source tail-env
                        (c#gen-prc source env (list loop-var)
                          (c#new-call source tail-env (ref loop-var)
                            (list (call '##structure-type (list (ref (car vars)))))))
                        (list
                         (c#gen-prc source env (list descriptor)
                           (c#new-tst source env
                             (call '##eq? (list (call '##type-id (list (ref descriptor)))
                                              (ref (cadr vars))))
                             (c#new-cst source env #t)
                             (c#new-call source tail-env
                               (c#gen-prc source env (list super)
                                 (c#new-tst source env (ref super)
                                   (c#new-call source tail-env (ref loop-var) (list (ref super)))
                                   (c#new-cst source env #f)))
                               (list (call '##type-super (list (ref descriptor))))))))))
                    (set! gb-structure-expansions (+ gb-structure-expansions 1))
                    (c#gen-prc source env vars
                      (let ((body
                             (c#new-tst source env
                               (call '##structure? (list (ref (car vars))))
                               (gen-loop)
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
