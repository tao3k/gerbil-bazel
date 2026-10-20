;; Transform only the frozen separate compiler's success cleanup list.
(define changed 0)
(define platform-expression
  (if (equal? (getenv "RETAINED_ENTRY_C_PLATFORM" #f) "1")
      '((c-lambda () bool
          "#if defined(__APPLE__) && defined(__MACH__) && defined(__GNUC__) && !defined(__clang__)\n___result = 1;\n#else\n___result = 0;\n#endif"))
      '(gxc#darwin-gnu-source-loader-platform?)))
(define cleanup
  '(cons _%output-c276294%_
     (cons _%output_-c276298%_
       (cons _%output-o276296%_ (cons _%output_-o276300%_ '())))))
(define (rewrite tree)
  (cond
    ((equal? tree cleanup)
     (set! changed (+ changed 1))
     `(if (and ,platform-expression
               (equal? (##getenv "GAMBIT_DARWIN_STATIC_OBJECT_REUSE" #f) "1")
               (equal? (##getenv "GAMBIT_DARWIN_RETAIN_ENTRY_OBJECTS" #f) "1"))
        (cons _%output-c276294%_ (cons _%output_-c276298%_ '()))
        ,tree))
    ((not (pair? tree)) tree)
    ((eq? (car tree) 'quote) tree)
    (else (cons (rewrite (car tree)) (rewrite (cdr tree))))))
(define forms
  (call-with-input-file (getenv "FD_DRIVER_INPUT")
    (lambda (input)
      (let loop ((result '()))
        (let ((form (read input)))
          (if (eof-object? form) (reverse result)
              (loop (cons (rewrite form) result))))))))
(if (not (= changed 1)) (error "exactly one frozen entry cleanup required" changed))
(define output (getenv "FD_DRIVER_OUTPUT"))
(if (file-exists? output) (error "fresh transformed output required"))
(call-with-output-file output
  (lambda (port) (for-each (lambda (form) (write form port) (newline port)) forms)))
(display "RETAINED-ENTRY-CLEANUP-OK exact-one-site default-off Darwin-GNU-only")
(newline)
