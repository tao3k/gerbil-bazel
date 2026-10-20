;; Read data, never evaluate a shell-created request.
(define (run-generated-c-request!)
  (let* ((request (getenv "GAMBIT_GENERATION_REQUEST"))
         (fields
           (call-with-input-file request
             (lambda (port)
               (let loop ((fields '()) (chars '()))
                 (let ((char (read-char port)))
                   (cond ((eof-object? char)
                          (if (pair? chars) (error "unterminated generation request"))
                          (reverse fields))
                         ((char=? char #\nul)
                          (loop (cons (list->string (reverse chars)) fields) '()))
                         (else (loop fields (cons char chars))))))))))
    (setenv "GAMBIT_GENERATION_REQUEST")
    (setenv "GAMBIT_GENERATION_ADAPTER_BIN")
    (if (not (= (length fields) 6)) (error "invalid generation request"))
    (let* ((bin (list-ref fields 0)) (input (list-ref fields 1))
           (output (list-ref fields 2)) (alias (list-ref fields 3))
           (target (list-ref fields 4)) (work (list-ref fields 5))
           (options (append
                      (list (list 'module-ref (string->symbol alias)) (list 'linker-name alias))
                      (if (string=? target "C") '((target C)) '())))
           (tools (map (lambda (name) (string-append bin "/" name))
                       '("gsc-original" "gsc" "gambit-file-sha256"
                         "gambit-generated-c-reads.scm" "gambit-generated-c-closure.scm"
                         "gambit-generated-c-adapter.scm"))))
      (if (not (or (string=? target "") (string=? target "C")))
          (error "invalid target request"))
      (reuse-generated-c-closure! (list input) options (path-directory output) work
        (string-append output ".generation-proof") (string-append bin "/gambit-file-sha256") tools))))
