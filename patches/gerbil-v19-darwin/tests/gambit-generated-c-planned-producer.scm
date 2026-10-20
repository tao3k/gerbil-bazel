;; CLI-local admission policy, not a compiler transformation or shared env edit.
(define generated-c-native-producer-request? #f)

(define (generated-c-native-select-producer-options options)
  (let loop ((rest options) (ordinary '()) (requests 0))
    (if (null? rest)
        (begin
          (if (> requests 1) (error "duplicate generated-C proof request"))
          (set! generated-c-native-producer-request? (= requests 1))
          (reverse ordinary))
        (if (equal? (car rest) '(generated-c-proof))
            (loop (cdr rest) ordinary (+ requests 1))
            (loop (cdr rest) (cons (car rest) ordinary) requests)))))

(let ((produce generated-c-native-compile-file-to-target))
  (set! generated-c-native-compile-file-to-target
    (lambda (file #!key options output)
      (if generated-c-native-producer-request?
          (produce file options: options output: output)
          (compile-file-to-target file options: options output: output)))))
