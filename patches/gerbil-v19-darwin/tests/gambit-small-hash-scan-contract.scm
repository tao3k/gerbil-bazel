(declare (standard-bindings) (extended-bindings) (not safe))

(define original-ref
  (c-lambda (scheme-object scheme-object) scheme-object
    "___result=___EXT(___gc_hash_table_ref)(___arg1,___arg2);"))
(define force-rehash
  (c-lambda (scheme-object) void
    "___GCHASHTABLE_FLAGS_FIELD(___arg1)=___FIXIOR(___GCHASHTABLE_FLAGS_FIELD(___arg1),___FIX(___GCHASHTABLE_FLAG_KEY_MOVED));"))
(define remove-entry
  (c-lambda (scheme-object scheme-object) void
    "___EXT(___gc_hash_table_set)(___arg1,___arg2,___ABSENT);"))
(define put-entry
  (c-lambda (scheme-object scheme-object scheme-object) void
    "___EXT(___gc_hash_table_set)(___arg1,___arg2,___arg3);"))
(define table-slots
  (c-lambda (scheme-object) scheme-object
    "___result=___FIX((___INT(___GCHASHTABLELENGTH(___arg1))-___GCHASHTABLE_KEY0)/2);"))

(define check-number 0)
(define (##gb-tree-check value)
  (set! check-number (+ check-number 1))
  (if (not value) (error "small hash scan contract failed" check-number)))
(define (compare-ref table key)
  (let ((expected (original-ref table key)))
    (##gb-tree-check (eq? (##gc-hash-table-ref table key) expected))))
(define (new-table n flags)
  (##gc-hash-table-allocate n flags (f64vector 0.2 0.5 0.7)))

(define (##gb-tree-run)
  (set! check-number 0)
  (let ((small (new-table 4 0))
        (large (new-table 40 0))
        (value (cons 17 23)))
    (##gb-tree-check (>= (table-slots small) 4))
    (for-each (lambda (key) (compare-ref small key)) '(0 1 2 3 4 5 6 7))
    (put-entry small 1 #f)
    (put-entry small 2 value)
    (put-entry small 3 43)
    (let loop ((i 0))
      (if (< i 512)
          (begin (compare-ref small (modulo i 8)) (loop (+ i 1)))))
    (##gb-tree-check (eq? (##gc-hash-table-ref small 2) value))
    (set-car! value 31)
    (##gb-tree-check (= (car (##gc-hash-table-ref small 2)) 31))
    (put-entry small 1 value)
    (compare-ref small 1)
    (remove-entry small 2)
    (compare-ref small 2)
    (put-entry small 4 59)
    (compare-ref small 4)
    (force-rehash small)
    (compare-ref small 1)
    (##gc)
    (compare-ref small 1)
    (put-entry large 1 value)
    (for-each (lambda (key) (compare-ref large key)) '(0 1 2 3 4 5 6 7))
    (let ((weak (new-table 4 19))
          (key (cons 101 103))
          (item (cons 107 109)))
      (put-entry weak key item)
      (compare-ref weak key)
      (##gc)
      (compare-ref weak key)
      (##gb-tree-check (eq? (##gc-hash-table-ref weak key) item)))
    #t))
