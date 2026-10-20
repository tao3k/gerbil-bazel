;; Diagnostic wrapper only. Preserve the original return-value arity.
(def original-module-reader (##eval 'gx#core-read-module))
(def module-read-rows '())
(def (observed-module-reader path)
  (let ((start (time->seconds (current-time))) (before (##process-statistics)))
    (call-with-values
     (lambda () (original-module-reader path))
     (lambda result
       (let (after (##process-statistics))
         (set! module-read-rows
           (cons (list path (- (time->seconds (current-time)) start)
                       (- (f64vector-ref after 7) (f64vector-ref before 7)))
                 module-read-rows)))
       (apply values result)))))
(##eval `(set! gx#core-read-module ',observed-module-reader))
(def (emit-module-read-probe!)
  (for-each
   (lambda (row)
     (display "MODULE-READ\t")
     (display (cadr row)) (display "\t") (display (caddr row)) (display "\t")
     (displayln (car row)))
   (reverse module-read-rows)))
