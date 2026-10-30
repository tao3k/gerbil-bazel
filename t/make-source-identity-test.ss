;;; Native metadata preserves expansion, linked identities and compiled consumers.
(import (prefix-in :std/make native.)
        :gerbil/compiler :gerbil/expander
        (only-in :std/io/tempfile call-with-temporary-directory)
        (only-in :std/misc/process run-process)
        (only-in :std/misc/ports read-all-as-string))
(extern namespace: std/make source-module-id)
(def (require! value message) (unless value (error message)))
(call-with-temporary-directory "native-make-identity"
  (lambda (root)
    (def (write! name text)
      (call-with-output-file (path-expand name root) (cut display text <>)))
    (write! "gerbil.pkg" "(package: native-make-contract)\n")
    (write! "inert.ss"
      "(begin-syntax (error \"expansion must not run during identity discovery\"))\n(export answer) (def answer 42)\n")
    (def inert (path-expand "inert.ss" root))
    (require! (eq? (source-module-id inert) 'native-make-contract/inert)
              "native header identity mismatch")
    (def old-expanded? #f)
    (with-catch (lambda (_) (set! old-expanded? #t))
      (lambda () (expander-context-id (core-import-module inert))))
    (require! old-expanded? "old expansion oracle did not execute the failing macro")
    (for-each
      (lambda (entry)
        (write! (car entry) (cadr entry))
        (def path (path-expand (car entry) root))
        (require! (eq? (source-module-id path) (caddr entry)) "declared identity mismatch")
        (require! (eq? (source-module-id path) (expander-context-id (core-import-module path)))
                  "reader identity differs from independent native expansion"))
      '(("plain.ss" "(export answer) (def answer 41)\n" native-make-contract/plain)
        ("explicit.ss" "package: another/package\nnamespace: alternate\n(export answer) (def answer 42)\n" another/package/explicit)
        ("unqualified.ss" "package: another/package\nnamespace: #f\n(export answer) (def answer 43)\n" another/package/unqualified)))
    ;; Native path resolution remains authoritative for linked source files.
    (create-directory (path-expand "alias" root))
    (write! "alias/gerbil.pkg" "(package: lexical-alias)\n")
    (def linked (path-expand "alias/linked.ss" root))
    (create-symbolic-link (path-expand "plain.ss" root) linked)
    (require! (eq? (source-module-id linked)
                  (expander-context-id (core-import-module linked)))
              "linked source identity differs from native expansion")
    ;; A custom reader is not assumed pure or called twice for metadata.
    (def marker (path-expand "reader-events" root))
    (write! "reader.ss"
      (call-with-output-string
        (lambda (port)
          (write '(import :gerbil/core) port) (newline port)
          (write '(export (import: :gerbil/core) (for-syntax read-module-body)) port)
          (newline port)
          (write `(begin-syntax
                    (def (read-module-body input)
                      (call-with-output-file (list path: ,marker append: #t)
                        (lambda (output) (display "read\n" output)))
                      (read-all input read-syntax))) port))))
    (write! "custom.ss"
      (call-with-output-string
        (lambda (port)
          (display "#lang " port)
          (write (path-expand "reader.ss" root) port)
          (display "\n(export answer) (def answer 44)\n" port))))
    (def custom (path-expand "custom.ss" root))
    (require! (eq? (source-module-id custom) 'native-make-contract/custom)
              "custom reader identity mismatch")
    (require! (eq? (source-module-id custom)
                  (expander-context-id (core-import-module custom)))
              "cached custom reader identity mismatch")
    (require! (equal? (call-with-input-file marker read-all-as-string) "read\n")
              "custom reader was executed more than once")
    (write! "consumer.ss" "(import ./plain) (export result) (def result (+ answer 1))\n")
    (def output (path-expand "out" root))
    (native.make '("plain" "consumer") srcdir: root libdir: output
      bindir: (path-expand "bin" root) prefix: "native-make-contract"
      parallelize: 2 verbose: #t)
    (def result
      (run-process
        (list "env" (string-append "GERBIL_LOADPATH=" output)
              "gxi" "-:max-heap=2G,debug=q" "-e"
              "(import :native-make-contract/consumer) (unless (= result 42) (error \"compiled consumer mismatch\")) (displayln \"NATIVE-MAKE-CONSUMER-OK\")")
        stdout-redirection: #t coprocess: read-all-as-string))
    (require! (string-contains result "NATIVE-MAKE-CONSUMER-OK") "compiled consumer receipt missing")))
(displayln "NATIVE-MAKE-SOURCE-IDENTITY-OK")
