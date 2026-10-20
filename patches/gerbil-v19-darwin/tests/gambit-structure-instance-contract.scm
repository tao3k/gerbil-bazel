(declare (extended-bindings) (standard-bindings))
(c-declare "#include \"gambit-structure-instance-probe.h\"")
(c-declare #<<c-end
static int probe_state(___SCMOBJ obj, ___SCMOBJ id) {
  ___WORD answer;
  return gambit_structure_probe(obj, id, &answer) ? (answer == ___TRU) : -1;
}
c-end
)
(define probe-state (c-lambda (scheme-object scheme-object) int "probe_state"))
(define reference ##structure-instance-of?)
(define checks 0)
(define (assert-equal actual expected)
  (if (not (equal? actual expected)) (error "structure predicate contract" actual expected))
  (set! checks (+ checks 1)))
(define (descriptor id super)
  (##structure ##type-type id 'probe 26 super '#()))
(define ids (list->vector '(t0 t1 t2 t3 t4 t5 t6 t7 t8 t9 t10 t11)))
(define types
  (let loop ((n 0) (super #f) (result '()))
    (if (= n 12)
        (list->vector (reverse result))
        (let ((next (descriptor (vector-ref ids n) super)))
          (loop (+ n 1) next (cons next result))))))
(define objects
  (append '(#f #t () 0 1 1.5 symbol "text" #(1 2) (1 . 2))
          (let loop ((n 0) (result '()))
            (if (= n 12) result
                (loop (+ n 1) (cons (##structure (vector-ref types n) n) result))))))

(let repeat ((n 0))
  (if (< n 20)
      (begin
        (for-each
         (lambda (obj)
           (for-each
            (lambda (id)
              (assert-equal (##structure-instance-of? obj id) (reference obj id)))
            (append (vector->list ids) '(missing 0 #f))))
         objects)
        (##gc)
        (repeat (+ n 1)))))

(assert-equal (probe-state (##structure (vector-ref types 11)) 't11) 1)
(assert-equal (probe-state (##structure (vector-ref types 11)) 't0) -1)
(assert-equal (probe-state (##structure (vector-ref types 11)) 'missing) -1)
(assert-equal (probe-state 123 'missing) 0)
(let ((cycle (descriptor 'cycle #f)))
  (##unchecked-structure-set! cycle cycle 4 ##type-type #f)
  (assert-equal (probe-state (##structure cycle) 'missing) -1)
  (assert-equal (##structure-instance-of? (##structure cycle) 'cycle) #t)
  (let ((obj (##structure cycle)))
    (for-each
     (lambda (predicate)
       (##unchecked-structure-set! cycle cycle 4 ##type-type #f)
       (let ((worker (make-thread predicate)))
         (thread-start! worker)
         (thread-sleep! 0.01)
         (thread-interrupt! worker
           (lambda ()
             (##gc)
             (##unchecked-structure-set! cycle #f 4 ##type-type #f)))
         (assert-equal (thread-join! worker) #f)))
     (list (lambda () (##structure-instance-of? obj 'missing))
           (lambda () (reference obj 'missing))))))
(assert-equal
 (with-exception-catcher (lambda (exception) 'caught)
   (lambda () (##structure-instance-of? 1)))
 'caught)
(if (< checks 6600) (error "missing structure predicate assertions" checks))
(display "STRUCTURE-INSTANCE-OK ")
(display checks)
(newline)
