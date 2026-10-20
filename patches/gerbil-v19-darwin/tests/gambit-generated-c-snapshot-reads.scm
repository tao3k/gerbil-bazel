;; Experimental replacement for the compiler's explicit four-argument reader.
;; Load the original journal first for its conservative macro-context classifier.
(set! record-generated-c-reads!
  (lambda (input options output scratch manifest)
    (if (file-exists? manifest) (error "fresh manifest required"))
    (let ((original ##read-all-as-a-begin-expr-from-path)
          (reads '()) (macro-context? #f) (count 0))
      (let ((result
             (dynamic-wind
               (lambda ()
                 (set! ##read-all-as-a-begin-expr-from-path
                   (lambda args
                     ;; GSC read-source supplies its original-container wrap
                     ;; and unwrap closures. Default port-derived locations are
                     ;; not admitted, nor are unrecognized reader call shapes.
                     (if (not (and (= (length args) 4)
                                   (string? (car args))
                                   (procedure? (caddr args))
                                   (procedure? (cadddr args))))
                         (error "unsupported snapshot compiler reader"))
                     (let* ((path (car args))
                            (snapshot (string-append scratch "/"
                                        (number->string count) (path-extension path))))
                       (set! count (+ count 1))
                       (copy-file path snapshot)
                       (set! reads (cons (list path snapshot) reads))
                       ;; Same suffix preserves start syntax; caller closures
                       ;; preserve original source locations and include bases.
                       (let ((source (apply original (cons snapshot (cdr args)))))
                         (if (not (and (vector? source) (= (vector-length source) 3)))
                             (error "unsupported compiler source-read result"))
                         (set! macro-context?
                           (or macro-context?
                               (generated-c-source-macro-context? (vector-ref source 1))))
                         (if macro-context? (set! generated-c-observed-macro-context? #t))
                         source)))))
               (lambda () (compile-file-to-target input options: options output: output))
               (lambda () (set! ##read-all-as-a-begin-expr-from-path original)))))
        (if (not result) (error "generation failed; no read manifest published"))
        (call-with-output-file manifest
          (lambda (port)
            (write (list 'generated-c-source-reads-v2 input options output
                         (reverse reads) (list 'source-macro-context macro-context?)) port)
            (newline port)))
        result))))
