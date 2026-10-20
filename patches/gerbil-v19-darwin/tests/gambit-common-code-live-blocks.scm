;;; Source-level prototype, not an installed compiler patch.
;;; Run with the GNU-GCC-built Gerbil V19 bin/gsc -e '(load "<this-file>")'.

(define (check name condition)
  (if (not condition) (error "check failed" name))
  (display name)
  (display ": OK\n"))

(define (live-count bbs)
  (let ((count 0))
    (c#bbs-for-each-bb (lambda (bb) (set! count (+ count 1))) bbs)
    count))

;; Keep the cheap legacy fast path; bound the actual comparison candidates
;; on sparse inputs without changing labels or the equivalence algorithm.
(define (common-code/live-budget bbs)
  (if (<= (c#bbs-next-lbl-num bbs) 300)
      (c#bbs-remove-common-code-aux bbs)
      (let* ((blocks (c#bbs-basic-blocks bbs))
             (length (c#stretchable-vector-length blocks)))
        (let loop ((index 0) (count 0))
          (cond ((> count 300) bbs)
                ((= index length) (c#bbs-remove-common-code-aux bbs))
                (else
                 (loop (+ index 1)
                       (+ count
                          (if (c#stretchable-vector-ref blocks index) 1 0)))))))))

(define frame (c#make-frame 0 '() '#() #f (c#varset-empty)))
(define return-operand (c#make-reg 0))

(define (return-block bbs label)
  (let ((bb (c#make-bb (c#make-label-simple label frame #f) bbs)))
    (c#bb-branch-instr-set!
     bb (c#make-jump return-operand #f #f #f #f frame #f))
    bb))

(define (fixture left right)
  (let* ((bbs (c#make-bbs))
         (entry (c#make-bb (c#make-label-simple 1 frame #f) bbs)))
    (return-block bbs left)
    (return-block bbs right)
    (c#bb-branch-instr-set!
     entry (c#make-ifjump 'fixture-test '() left right #f frame #f))
    (c#bbs-next-lbl-num-set! bbs (+ right 1))
    (c#bbs-entry-lbl-num-set! bbs 1)
    (c#bbs-determine-refs! bbs)
    bbs))

(define sparse (fixture 401 402))
(check 'sparse-has-three-live-blocks (= (live-count sparse) 3))
(check 'dead-cleanup-preserves-high-water
       (= (c#bbs-next-lbl-num (c#bbs-remove-dead-code sparse)) 403))
(check 'legacy-skips-sparse-common-code
       (eq? sparse (c#bbs-remove-common-code sparse)))
(define merged
  (c#bbs-remove-dead-code (common-code/live-budget sparse)))
(check 'candidate-merges-sparse-duplicate (= (live-count merged) 2))
(check 'candidate-preserves-high-water (= (c#bbs-next-lbl-num merged) 403))
(define merged-entry
  (c#bb-branch-instr (c#lbl-num->bb (c#bbs-entry-lbl-num merged) merged)))
(check 'both-arms-reference-same-surviving-block
       (= (c#ifjump-true merged-entry) (c#ifjump-false merged-entry)))
(check 'surviving-block-keeps-return-operand
       (eqv? return-operand
             (c#jump-opnd
              (c#bb-branch-instr
               (c#lbl-num->bb (c#ifjump-true merged-entry) merged)))))

(define dense-small (fixture 2 3))
(check 'legacy-small-merges
       (= (live-count (c#bbs-remove-dead-code
                       (c#bbs-remove-common-code dense-small))) 2))
(check 'candidate-small-merges
       (= (live-count (c#bbs-remove-dead-code
                       (common-code/live-budget (fixture 2 3)))) 2))

(define distinct (fixture 401 402))
(c#bb-branch-instr-set!
 (c#lbl-num->bb 402 distinct)
 (c#make-jump (c#make-reg 1) #f #f #f #f frame #f))
(check 'different-return-operands-do-not-merge
       (= (live-count (c#bbs-remove-dead-code
                       (common-code/live-budget distinct))) 3))

(define distinct-poll (fixture 401 402))
(c#bb-branch-instr-set!
 (c#lbl-num->bb 402 distinct-poll)
 (c#make-jump return-operand #f #f #t #f frame #f))
(check 'different-poll-requirements-do-not-merge
       (= (live-count (c#bbs-remove-dead-code
                       (common-code/live-budget distinct-poll))) 3))

(define (dense-fixture count)
  (let ((bbs (c#make-bbs)))
    (let loop ((label 1))
      (if (<= label count)
          (begin (return-block bbs label) (loop (+ label 1)))))
    (c#bbs-next-lbl-num-set! bbs (+ count 1))
    (c#bbs-entry-lbl-num-set! bbs 1)
    bbs))
(define at-budget (dense-fixture 300))
(check 'exact-live-budget-is-eligible
       (not (eq? at-budget (common-code/live-budget at-budget))))
(define over-budget (dense-fixture 301))
(check 'over-live-budget-still-skips
       (eq? over-budget (common-code/live-budget over-budget)))
(display "GVM-LIVE-BLOCK-GUARD-OK\n")
