;; Ordinary GSC APIs only. This tests a proposed cache boundary, not a cache.
(define (member-inputs)
  (call-with-input-file "inputs.txt"
    (lambda (port)
      (let loop ((result '()))
        (let ((line (read-line port)))
          (if (eof-object? line) (reverse result)
              (loop (cons line result))))))))

(define (compile-member input)
  (if (not (compile-file-to-target input options: '((target C))
             output: (string-append (path-strip-extension input) ".c")))
      (error "member compilation failed" input)))

(let ((inputs (member-inputs)) (mode (getenv "MEMBER_CONTROL_MODE")))
  (cond
    ((string=? mode "reverse")
     (for-each compile-member (reverse inputs)))
    ((string=? mode "one-change")
     (call-with-output-file (list path: (car inputs) append: #t)
       (lambda (port) (display "\n(define __member_cache_probe 29)\n" port)))
     (compile-member (car inputs)))
    (else (error "unknown member control mode" mode)))
  (display "GENERATED-C-MEMBER-CONTROL-OK ")
  (display mode) (display " modules=") (write (length inputs)) (newline))
