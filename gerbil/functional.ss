;;; Small, reusable extensions to the Gerbil standard library.
;;;
;;; This file intentionally contains only deterministic value operations.
;;; Environment, filesystem, process, policy, and receipt-schema effects stay
;;; with their domain owners. Consumers load this source library explicitly so
;;; Bazel can make its exact bytes part of the action identity.

(import :std/misc/hash)

(def (normalized-exit-code status)
  (cond
   ((< status 0) 1)
   ((> status 255) (quotient status 256))
   (else status)))

(def (positive-integer text)
  (let (value (and text (string->number text)))
    (and (exact-integer? value) (> value 0) value)))

(def (non-negative-integer text)
  (let (value (and text (string->number text)))
    (and
     (exact-integer? value)
     (>= value 0)
     value)))

(def (non-empty-string? value)
  (and
   (string? value)
   (> (string-length value) 0)))

(def (non-negative-exact-integer? value)
  (and
   (exact-integer? value)
   (>= value 0)))

(def (list-of? predicate value)
  (and
   (list? value)
   (andmap predicate value)))

(def (unique-items? items)
  (let (seen (make-hash-table))
    (let loop ((remaining items))
      (cond
       ((null? remaining) #t)
       ((hash-key? seen (car remaining)) #f)
       (else
        (hash-put! seen (car remaining) #t)
        (loop (cdr remaining)))))))

(def (tail-lines lines maximum)
  (let (count (length lines))
    (if (> count maximum)
        (list-tail lines (- count maximum))
        lines)))
