(def (check name value)
  (unless value (error "intern string contract failed" name))
  (displayln "CASE-OK " name)
  (force-output))

(def (same-name? text)
  (let ((a (string->symbol text)) (b (string->symbol (string-copy text))))
    (and (eq? a b) (equal? text (symbol->string a)))))

(check "empty" (same-name? ""))
(check "ascii" (same-name? "gb-intern-contract-short"))
(check "unicode"
  (same-name? (list->string (map integer->char '(955 20013 128512 1114111)))))
(check "embedded-nul"
  (same-name? (string-append "gb-intern" (string (integer->char 0)) "suffix")))
(check "long-and-tail-difference"
  (let* ((prefix (make-string 4096 #\x))
         (left (string-append prefix "a"))
         (right (string-append prefix "b")))
    (and (same-name? left) (same-name? right)
         (not (eq? (string->symbol left) (string->symbol right))))))
(check "mutable-input"
  (let* ((text (string-copy "gb-intern-mutable-a")) (before (string->symbol text)))
    (string-set! text (- (string-length text) 1) #\b)
    (and (equal? (symbol->string before) "gb-intern-mutable-a")
         (not (eq? before (string->symbol text))) (same-name? text))))
(check "keyword-identity"
  (let ((text (string-append "gb-intern-keyword-" (string (integer->char 955)))))
    (and (eq? (string->keyword text) (string->keyword (string-copy text)))
         (equal? text (keyword->string (string->keyword text))))))
(check "table-growth-and-gc"
  (let ((names (let loop ((i 0) (acc '()))
                 (if (= i 20000) acc
                   (let ((s (string-append "gb-intern-growth-" (number->string i))))
                     (loop (+ i 1) (cons (cons s (string->symbol s)) acc)))))))
    (##gc)
    (andmap (lambda (entry) (eq? (cdr entry) (string->symbol (string-copy (car entry))))) names)))
(displayln "OK intern-string-semantics")
(force-output)
