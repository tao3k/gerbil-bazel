(def original-module-import (gx#current-expander-module-import))
(def import-cost-rows '())
(def import-depth 0)
(def (observed-module-import path reload?)
  (let ((start (time->seconds (current-time))) (before (##process-statistics))
        (depth import-depth))
    (set! import-depth (+ import-depth 1))
    (try
      (original-module-import path reload?)
      (finally
        (set! import-depth depth)
        (let (after (##process-statistics))
          (set! import-cost-rows
            (cons (list depth (- (time->seconds (current-time)) start)
                        (- (f64vector-ref after 7) (f64vector-ref before 7)) path)
                  import-cost-rows)))))))
(gx#current-expander-module-import observed-module-import)
(def (emit-module-import-probe!)
  (for-each
   (lambda (row)
     (display "MODULE-IMPORT\t") (display (car row)) (display "\t")
     (display (cadr row)) (display "\t") (display (caddr row)) (display "\t")
     (write (cadddr row)) (newline))
   (reverse import-cost-rows)))
