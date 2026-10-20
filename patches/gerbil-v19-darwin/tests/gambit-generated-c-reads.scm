;; Source-read journal only; not a complete cache-admission proof.
(define generated-c-observed-macro-context? #f)
(define (generated-c-source-macro-context? value)
  (define (unwrap x) (if (##source? x) (##source-code x) x))
  (let ((value (unwrap value)))
    (and (pair? value)
         (let ((head (unwrap (car value))))
           (cond
             ((memq head '(quote ##quote)) #f)
             ((memq head '(define-macro ##define-macro define-syntax ##define-syntax
                           namespace ##namespace macro-scope ##macro-scope)) #t)
             (else
               (or (generated-c-source-macro-context? (car value))
                   (generated-c-source-macro-context? (cdr value)))))))))

(define (record-generated-c-reads! input options output scratch manifest)
  (if (file-exists? manifest) (error "fresh manifest required"))
  (let ((original ##read-all-as-a-begin-expr-from-path)
        (reads '())
        (macro-context? #f)
        (count 0))
    (let ((result
           (dynamic-wind
             (lambda ()
               (set! ##read-all-as-a-begin-expr-from-path
                 (lambda args
                   (let* ((path (car args))
                          (snapshot (string-append scratch "/"
                                      (number->string count) ".source")))
                     (set! count (+ count 1))
                     (copy-file path snapshot)
                     (set! reads (cons (list path snapshot) reads))
                     (let ((source (apply original args)))
                       (if (not (and (vector? source) (= (vector-length source) 3)))
                           (error "unsupported compiler source-read result"))
                       (set! macro-context?
                         (or macro-context?
                             (generated-c-source-macro-context? (vector-ref source 1))))
                       (if macro-context? (set! generated-c-observed-macro-context? #t))
                       source)))))
             (lambda ()
               (compile-file-to-target input options: options output: output))
             (lambda ()
               (set! ##read-all-as-a-begin-expr-from-path original)))))
      (if (not result) (error "generation failed; no read manifest published"))
      (call-with-output-file manifest
        (lambda (port)
          (write (list 'generated-c-source-reads-v2 input options output
                       (reverse reads) (list 'source-macro-context macro-context?)) port)
          (newline port)))
      result)))

(define (record-paired-generated-c-reads! directory output scratch)
  (let ((count 0))
    (for-each
      (lambda (name)
        (let ((size (string-length name)))
          (if (and (> size 4)
                   (string=? (substring name (- size 4) size) ".scm"))
              (let* ((stem (substring name 0 (- size 4)))
                     (input (string-append directory "/" name))
                     (private (string-append output "/" stem ".c"))
                     (snapshots (string-append scratch "/" stem)))
                (create-directory snapshots)
                (record-generated-c-reads! input '() private snapshots
                  (string-append private ".reads"))
                (set! count (+ count 1))))))
      (directory-files directory))
    (display "GENERATED-C-READS-BATCH-OK modules=")
    (display count)
    (newline)))
