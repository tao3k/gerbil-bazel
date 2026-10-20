(declare (standard-bindings) (extended-bindings))

(define checks 0)
(define (check actual expected)
  (if (not (equal? actual expected))
      (error "keyword outline contract failed" actual expected))
  (set! checks (+ checks 1)))

(define (raises? thunk)
  (with-exception-catcher (lambda (exception) #t)
    (lambda () (thunk) #f)))

(define (keys #!key (a 10) (b 20)) (list a b))
(define (rest-before a #!rest r #!key k) (list a k r))
(define (rest-after a #!key k #!rest r) (list a k r))

(check (keys) '(10 20))
(check (keys b: 7 a: 3) '(3 7))
(check (keys a: 3 a: 4) '(3 20))
(check (raises? (lambda () (keys z: 1))) #t)
(check (raises? (lambda () (keys a:))) #t)
(check (raises? (lambda () (keys 1))) #t)
(check (rest-before 7 k: 8 9) '(7 8 (k: 8 9)))
(check (rest-before 7 k: 8 z: 9) '(7 8 (k: 8 z: 9)))
(check (rest-after 7 k: 8 9) '(7 8 (9)))
(check (raises? (lambda () (rest-after 7 k: 8 z: 9))) #t)

(define (range n)
  (let loop ((i n) (out '()))
    (if (= i 0) out (loop (- i 1) (cons i out)))))
(define tail (range 500))
(define arguments (append '(7 k: 8) tail))
(let loop ((i 1500))
  (if (> i 0)
      (begin
        (check (apply rest-after arguments) (list 7 8 tail))
        (if (= (modulo i 25) 0) (##gc))
        (loop (- i 1)))))

(check (call-with-current-continuation
        (lambda (escape) (escape (keys a: 42 b: 43))))
       '(42 43))

(c-declare "int outline_scheme_callback(int);
static int outline_call_callback(int x) {
  return outline_scheme_callback(x);
}")
(c-define (outline-scheme-callback x) (int) int "outline_scheme_callback" ""
  (+ x (car (keys a: 3))))
(define call-native
  (c-lambda (int) int "outline_call_callback"))
(check (call-native 11) 14)

(display "KEYWORD-OUTLINE-OK ")
(display checks)
(newline)
