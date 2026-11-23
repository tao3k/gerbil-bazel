;;; Native CLI workers must preserve the sequential index and original failures.
(import (only-in :gerbil/tools/gxtags make-tags)
        (only-in :std/misc/process run-process/batch)
        (only-in :std/string/path path-default-extension))

(def root (path-expand "parallel" (getenv "SDK_TAG_TEST_ROOT")))
(create-directory* root)
(def (path name extension)
  (path-expand (path-default-extension name extension) root))
(def (write-source file forms)
  (call-with-output-file file
    (lambda (output)
      (for-each (lambda (form) (write form output) (newline output)) forms))))
(def sources
  (map
    (lambda (name)
      (let (file (path (symbol->string name) ".ss"))
        (write-source file `((export answer λ-answer)
                            (def answer ',name) (def λ-answer answer)))
        file))
    '(alpha beta gamma delta epsilon zeta)))
(def ordered (append sources (list (car sources))))
(def expected (path "expected" ".tags"))
(def actual (path "actual" ".tags"))
(def (check-index)
  (unless (equal? (read-file-string expected) (read-file-string actual))
    (error "parallel native CLI changed index bytes or ordering")))
(def (cli args)
  (run-process/batch (cons "gxtags" args)))

(for-each
  (lambda (format)
    (make-tags ordered expected #f format)
    (for-each
      (lambda (jobs)
        (cli (append ["--jobs" jobs "-o" actual "-t" (symbol->string format)] ordered))
        (check-index))
      '("1" "3"))
    ;; The default owns machine-derived capacity; no fixed worker cap is added.
    (cli (append ["-o" actual "-t" (symbol->string format)] ordered))
    (check-index)
    (make-tags sources expected #f format)
    (make-tags sources actual #f format)
    (make-tags sources expected #t format)
    (cli (append ["--jobs" "3" "-a" "-o" actual "-t" (symbol->string format)] sources))
    (check-index))
  '(emacs vim))

;; An explicit empty ordered list is empty input, never an implicit cwd scan.
(def empty (path "empty" ".inputs"))
(write-source empty '(()))
(cli ["--source-list" empty "--jobs" "3" "-o" actual])
(unless (equal? (read-file-string actual) "")
  (error "empty source list scanned unrelated sources"))

(def (check-refused args)
  (write-file-string actual "previous complete index")
  (def refused? #f)
  (with-catch
    (lambda (_) (set! refused? #t))
    (lambda () (cli (append ["-o" actual] args))))
  (unless (and refused? (equal? (read-file-string actual) "previous complete index"))
    (error "native CLI failure published a partial index")))
(check-refused ["--jobs" "0" (car sources)])
(write-source empty (list sources '(unexpected trailing input)))
(check-refused ["--source-list" empty "--jobs" "3"])

;; This real macro removes its own temporary source after expansion. A worker
;; must then fail when the tag writer reads source lines. No fault hook or fake
;; child executable participates; other workers still have to be reaped.
(def doomed (path "removed-after-expansion" ".ss"))
(write-source doomed
  `((import (for-syntax :gerbil/runtime/gambit))
    (begin-syntax (delete-file ,doomed))
    (export answer) (def answer 42)))
(check-refused ["--jobs" "3" (car sources) doomed])
(unless (not (file-exists? doomed))
  (error "worker failure did not reach the real expansion/write boundary"))
(displayln "NATIVE-TAGS-PARALLEL-OK")
