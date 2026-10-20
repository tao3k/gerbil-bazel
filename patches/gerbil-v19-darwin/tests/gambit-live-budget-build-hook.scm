;;; Experimental evaluator hook: both modes use the same observation overhead.
(define d881-mode (getenv "D881_MODE"))
(define d881-original c#bbs-remove-common-code)
(define d881-total 0)
(define d881-sparse 0)
(define d881-changed 0)
(define d881-removed 0)
(define d881-pending-live #f)
(define (d881-count bbs)
  (let ((n 0))
    (c#bbs-for-each-bb (lambda (bb) (set! n (+ n 1))) bbs)
    n))
(set! c#bbs-remove-common-code
  (lambda (bbs)
    (set! d881-total (+ d881-total 1))
    (if (<= (c#bbs-next-lbl-num bbs) 300)
        (d881-original bbs)
        (let ((live (d881-count bbs)))
          (if (> live 300)
              bbs
              (begin
                (set! d881-sparse (+ d881-sparse 1))
                (if (equal? d881-mode "candidate")
                    (let ((result (c#bbs-remove-common-code-aux bbs)))
                      (if (not (eq? result bbs))
                          (begin
                            (set! d881-changed (+ d881-changed 1))
                            (set! d881-pending-live live)))
                      result)
                    bbs)))))))
;; The compiled front end calls purify-procs through a global binding, but
;; compiled GVM-to-GVM calls use direct jumps and bypass a replaced binding.
(set! c#purify-procs
  (lambda (procs)
    (for-each
     (lambda (proc)
       (let ((bbs (c#proc-obj-code proc)))
         (if (c#bbs? bbs)
             (c#proc-obj-code-set!
              proc
              (let loop ((bbs1 bbs))
                (let* ((bbs2 (c#bbs-remove-jump-cascades bbs1))
                       (bbs3 (c#bbs-remove-dead-code bbs2)))
                  (if d881-pending-live
                      (begin
                        (set! d881-removed
                          (+ d881-removed (- d881-pending-live (d881-count bbs3))))
                        (set! d881-pending-live #f)))
                  (let* ((bbs4 (c#bbs-remove-common-code bbs3))
                         (bbs5 (c#bbs-remove-useless-jumps bbs4)))
                  (if (not (eq? bbs3 bbs5))
                      (loop bbs5)
                      (c#bbs-order bbs5)))))))))
     procs)
    procs))
(##add-exit-job!
 (lambda ()
   (let ((port (current-error-port)))
     (display "D881-STATS " port)
     (write (list d881-mode d881-total d881-sparse d881-changed d881-removed) port)
     (newline port))))
