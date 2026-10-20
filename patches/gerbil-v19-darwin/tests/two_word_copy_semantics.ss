(def (check name value)
  (unless value (error "GC copy contract failed" name))
  (displayln "CASE-OK " name)
  (force-output))

(check "shared-pair"
  (let* ((pair (cons 19 23)) (root (vector pair pair)))
    (##gc)
    (and (eq? (vector-ref root 0) (vector-ref root 1))
         (= (car (vector-ref root 0)) 19) (= (cdr (vector-ref root 0)) 23))))
(check "cyclic-pair"
  (let ((pair (cons 31 #f)))
    (set-cdr! pair pair)
    (##gc)
    (and (= (car pair) 31) (eq? pair (cdr pair)))))
(check "two-word-vector"
  (let* ((child (cons 41 43)) (v (vector child child)))
    (##gc)
    (set-car! (vector-ref v 0) 47)
    (and (eq? (vector-ref v 0) (vector-ref v 1)) (= (car (vector-ref v 1)) 47))))
(check "two-word-string"
  (let ((s (list->string (map integer->char '(65 955 20013 128512)))))
    (##gc)
    (equal? (map char->integer (string->list s)) '(65 955 20013 128512))))
(check "other-size-fallback"
  (let ((objects (map (lambda (n) (make-vector n n)) '(0 1 3 4 5 8 9 32 1024))))
    (##gc)
    (andmap (lambda (v) (andmap (lambda (x) (= x (vector-length v))) (vector->list v))) objects)))
(check "closure-roots"
  (let* ((data (vector 53 59)) (get (lambda () data)))
    (##gc)
    (equal? (get) '#(53 59))))
(check "continuation-roots"
  (let* ((data (cons 61 67))
         (result (call/cc (lambda (return) (##gc) (return data)))))
    (and (eq? data result) (= (car result) 61) (= (cdr result) 67))))
(check "weak-live-roots"
  (let ((tab (##gc-hash-table-allocate 4 19 '#f64(.2 .5 .7)))
        (key (cons 71 73)) (value (vector 79 83)))
    (##gc-hash-table-set! tab key value)
    (##gc)
    (eq? value (##gc-hash-table-ref tab key))))
(check "repeated-copy-stress"
  (let loop ((round 0))
    (if (= round 24) #t
      (let ((roots (map (lambda (i) (vector (cons i round) (cons round i))) (iota 10000))))
        (##gc)
        (and (andmap (lambda (v)
                       (let ((a (vector-ref v 0)) (b (vector-ref v 1)))
                         (and (= (car a) (cdr b)) (= (cdr a) round) (= (car b) round)))) roots)
             (loop (+ round 1)))))))
(displayln "OK two-word-copy-semantics")
(force-output)
