(define checks 0)
(define (assert-equal actual expected)
  (if (not (equal? actual expected)) (error "register bridge contract" actual expected))
  (set! checks (+ checks 1)))

(define (hash-round n)
  (let* ((table (make-hash-table-eq))
         (values (list n (+ n 1) (+ n 2) (+ n 3) (+ n 4))))
    (hash-put! table 'bridge values)
    (##gc)
    (assert-equal (hash-ref table 'bridge) values)
    (assert-equal (apply list (hash-ref table 'bridge)) values)
    n))

(c-define (bridge-callback n) (int) int "gambit_bridge_callback" ""
  (hash-round n))
(c-declare #<<c-end
extern int gambit_bridge_callback(int);
static int bridge_bounce(int n) { return gambit_bridge_callback(n); }
c-end
)
(define bridge-bounce (c-lambda (int) int "bridge_bounce"))

(let loop ((n 0))
  (if (< n 300)
      (begin
        (assert-equal (hash-round n) n)
        (if (= (modulo n 10) 0)
            (assert-equal (bridge-bounce n) n))
        (loop (+ n 1)))))

(assert-equal
 (call-with-current-continuation
  (lambda (escape)
    (let ((table (make-hash-table-eq)))
      (hash-put! table 'escape escape)
      (##gc)
      ((hash-ref table 'escape) 'escaped))))
 'escaped)
(assert-equal
 (with-exception-catcher
  (lambda (exception) 'caught)
  (lambda () (hash-ref (make-hash-table-eq) 'missing)))
 'caught)
(if (< checks 900) (error "missing register bridge assertions" checks))
(display "REGISTER-BRIDGE-OK ")
(display checks)
(newline)
