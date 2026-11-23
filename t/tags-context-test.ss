;;; Native tag generation must release indexed source contexts, not exports.
(import :gerbil/expander
        (only-in :gerbil/tools/gxtags make-tags))

(def root (getenv "SDK_TAG_TEST_ROOT"))
(def source-a (path-expand "source-a.ss" root))
(def source-b (path-expand "source-b.ss" root))
(def malformed (path-expand "malformed.ss" root))
(def together (path-expand "together.tags" root))
(def separate (path-expand "separate.tags" root))

(write-file-string source-a
  "(export value λ-value increment)\n(def value 42)\n(def λ-value 7)\n(defrules increment () ((_ x) (+ x 1)))\n")
(write-file-string source-b
  "(import \"source-a\")\n(export value answer)\n(def answer (increment value))\n")
(write-file-string malformed "(def broken\n")

(def saved-registry (hash-copy __module-registry))

(def (check-registry)
  (unless (= (hash-length __module-registry) (hash-length saved-registry))
    (error "tag generation retained source module contexts"))
  (hash-for-each
    (lambda (key value)
      (unless (eq? value (hash-ref __module-registry key))
        (error "tag generation changed a caller-owned context" key)))
    saved-registry))

;; Include a macro import, re-export, non-ASCII identifier and unreadable source.
;; Independent per-file generation must yield exactly the same bytes and offsets.
(make-tags [source-a source-b malformed] together)
(check-registry)
(make-tags [source-a] separate)
(check-registry)
(make-tags [source-b] separate #t)
(check-registry)
(make-tags [malformed] separate #t)
(check-registry)
(unless (equal? (read-file-string together) (read-file-string separate))
  (error "tag content or source offsets changed across input grouping"))
(for-each
  (lambda (name)
    (unless (string-contains (read-file-string together) name)
      (error "exported tag missing" name)))
  ["value" "λ-value" "increment" "answer"])

;; UTF-8 source bytes, rather than character counts, determine this offset.
(unless (string-contains
          (read-file-string together)
          (string-append "(def λ-value 7)" (string #\x7f)
                         "λ-value" (string #\x01) "3,49\n"))
  (error "independent UTF-8 source offset oracle failed"))

(make-tags [source-a source-b] together #f 'vim)
(check-registry)
(make-tags [source-b source-a] separate #f 'vim)
(check-registry)
(unless (equal? (read-file-string together) (read-file-string separate))
  (error "sorted Vim tags depend on source traversal order"))

;; A rejected format must preserve both the file and the caller registry.
(def before (read-file-string together))
(def rejected? #f)
(with-catch
  (lambda (_) (set! rejected? #t))
  (lambda () (make-tags [source-a] together #f 'invalid)))
(unless (and rejected? (equal? before (read-file-string together)))
  (error "invalid format did not preserve the destination"))
(check-registry)
(displayln "NATIVE-TAGS-CONTEXT-OK")
