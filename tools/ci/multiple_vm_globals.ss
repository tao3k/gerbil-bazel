(let loop ((i 0) (globals '()))
  (if (< i 32768)
      (let* ((id (string->symbol
                  (string-append "ci-multiple-vm-global-" (number->string i))))
             (global (##make-global-var id)))
        (unless (##unbound? (##global-var-ref global))
          (error "new global was not initialized as unbound" i))
        (##global-var-set! global (cons i (vector i)))
        (when (zero? (modulo i 1024))
          (##gc)
          (displayln "MULTIPLE-VM-GLOBALS " i))
        (loop (+ i 1) (cons id globals)))
      (begin
        (##gc)
        (let verify ((remaining globals) (expected (- i 1)))
          (if (null? remaining)
              (displayln "MULTIPLE-VM-GLOBALS-OK")
              (let ((value (##global-var-ref (car remaining))))
                (unless (and (pair? value)
                             (= (car value) expected)
                             (= (vector-ref (cdr value) 0) expected))
                  (error "global value lost after growth and GC" expected))
                (verify (cdr remaining) (- expected 1))))))))

(let ((workers
       (map (lambda (worker)
              (make-thread
               (lambda ()
                 (let loop ((i 0))
                   (when (< i 1024)
                     (let* ((id (string->symbol
                                 (string-append "ci-multiple-vm-thread-"
                                                (number->string worker) "-"
                                                (number->string i))))
                            (global (##make-global-var id)))
                       (##global-var-set! global (vector worker i))
                       (when (zero? (modulo i 128)) (##gc))
                       (loop (+ i 1))))))))
            '(0 1 2 3))))
  (for-each thread-start! workers)
  (for-each thread-join! workers)
  (for-each
   (lambda (worker)
     (let loop ((i 0))
       (when (< i 1024)
         (let* ((id (string->symbol
                     (string-append "ci-multiple-vm-thread-"
                                    (number->string worker) "-"
                                    (number->string i))))
                (value (##global-var-ref id)))
           (unless (and (vector? value)
                        (= (vector-length value) 2)
                        (= (vector-ref value 0) worker)
                        (= (vector-ref value 1) i))
             (error "threaded global value lost" worker i))
           (loop (+ i 1))))))
   '(0 1 2 3))
  (displayln "MULTIPLE-VM-THREADS-OK"))
