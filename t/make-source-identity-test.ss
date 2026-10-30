;;; Native metadata preserves expansion, linked identities and compiled consumers.
(import (prefix-in :std/make native.)
        :gerbil/compiler :gerbil/expander
        (only-in :std/sync/barrier make-barrier barrier-error! barrier-wait!)
        (only-in :std/io/tempfile call-with-temporary-directory)
        (only-in :std/misc/process run-process)
        (only-in :std/misc/ports read-all-as-string))
(def (require! value message) (unless value (error message)))
(call-with-temporary-directory "native-make-identity"
  (lambda (root)
    (def (write! name text)
      (call-with-output-file (path-expand name root) (cut display text <>)))
    (write! "gerbil.pkg" "(package: native-make-contract)\n")
    (write! "inert.ss"
      "(begin-syntax (error \"expansion must not run during identity discovery\"))\n(export answer) (def answer 42)\n")
    (def inert (path-expand "inert.ss" root))
    (require! (eq? (core-read-module-id inert) 'native-make-contract/inert)
              "native header identity mismatch")
    (require! (stx-pair? (core-read-module-declaration inert))
              "source declaration discovery expanded the inert module")
    (write! "explicit-inert.ss"
      "package: native-header-contract\n(begin-syntax (error \"explicit identity discovery expanded a body\"))\n(export answer) (def answer 42)\n")
    (def explicit-inert (path-expand "explicit-inert.ss" root))
    (require! (eq? (core-read-module-id explicit-inert)
                  'native-header-contract/explicit-inert)
              "explicit header identity discovery expanded a body")
    (def explicit-expanded? #f)
    (with-catch (lambda (_) (set! explicit-expanded? #t))
      (lambda () (expander-context-id (core-import-module explicit-inert))))
    (require! explicit-expanded? "independent explicit-header macro oracle did not fail")
    (def old-expanded? #f)
    (with-catch (lambda (_) (set! old-expanded? #t))
      (lambda () (expander-context-id (core-import-module inert))))
    (require! old-expanded? "old expansion oracle did not execute the failing macro")
    (for-each
      (lambda (entry)
        (write! (car entry) (cadr entry))
        (def path (path-expand (car entry) root))
        (require! (eq? (core-read-module-id path) (caddr entry)) "declared identity mismatch")
        (require! (eq? (core-read-module-id path) (expander-context-id (core-import-module path)))
                  "reader identity differs from independent native expansion"))
      '(("plain.ss" "(export answer) (def answer 41)\n" native-make-contract/plain)
        ("explicit.ss" "package: another/package\nnamespace: alternate\n(export answer) (def answer 42)\n" another/package/explicit)
        ("unqualified.ss" "package: another/package\nnamespace: #f\n(export answer) (def answer 43)\n" another/package/unqualified)))
    ;; Native path resolution remains authoritative for linked source files.
    (create-directory (path-expand "alias" root))
    (write! "alias/gerbil.pkg" "(package: lexical-alias)\n")
    (def linked (path-expand "alias/linked.ss" root))
    (create-symbolic-link (path-expand "plain.ss" root) linked)
    (require! (eq? (core-read-module-id linked)
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
    (require! (not (core-read-module-declaration custom))
              "opaque reader declarations must not be decoded for hints")
    (require! (eq? (core-read-module-id custom) 'native-make-contract/custom)
              "custom reader identity mismatch")
    (require! (eq? (core-read-module-id custom)
                  (expander-context-id (core-import-module custom)))
              "cached custom reader identity mismatch")
    (require! (equal? (call-with-input-file marker read-all-as-string) "read\n")
              "custom reader was executed more than once")
    ;; Failure presence is independent of its Scheme value, including #f.
    ;; Completion and a later error must not overwrite the first failure.
    (for-each
      (lambda (limit)
        (def barrier (make-barrier limit))
        (def seen? #f)
        (def observed 'missing)
        (barrier-error! barrier #f)
        (barrier-error! barrier 'later-error)
        (with-catch
          (lambda (error) (set! seen? #t) (set! observed error))
          (lambda () (barrier-wait! barrier)))
        (require! (and seen? (eq? observed #f))
                  "the first false barrier failure was lost or replaced"))
      '(0 1))
    ;; A source expansion failure must reach Make's caller, not its watchdog.
    ;; Write Scheme data so paths and source forms keep their native meaning.
    (for-each
      (lambda (entry)
        (def name (car entry))
        (write! (string-append name ".ss") (cadr entry))
        (def runner (path-expand (string-append name "-runner.ss") root))
        (call-with-output-file runner
          (lambda (port)
            (write
              `(begin
                 (import (prefix-in :std/make native.))
                 (def (main)
                   (def rejected? #f)
                   (with-catch
                     (lambda (error) (set! rejected? #t))
                     (lambda ()
                       (native.make (list ,name)
                         srcdir: ,root
                         libdir: ,(path-expand (string-append name "-lib") root)
                         bindir: ,(path-expand (string-append name "-bin") root)
                         parallelize: 1)))
                   (unless rejected? (error "source failure was admitted"))
                   (displayln "NATIVE-SOURCE-FAILURE-CAUGHT")))
              port)))
        (def output
          (run-process
            (list (getenv "SDK_NATIVE_TIMEOUT_PROGRAM" "timeout")
                  "--signal=TERM" "--kill-after=2s" "10s"
                  "gxi" "-:max-heap=2G,debug=q" runner)
            stderr-redirection: #t
            coprocess: (lambda (process)
                         (close-output-port process)
                         (read-all-as-string process))))
        (require! (and (string-contains output "NATIVE-SOURCE-FAILURE-BODY")
                       (string-contains output "NATIVE-SOURCE-FAILURE-CAUGHT"))
                  "source failure did not execute and reach the caller"))
      '(("coordinator-error"
         "(begin-syntax (displayln \"NATIVE-SOURCE-FAILURE-BODY\") (error \"native-source-error\"))\n")
        ("coordinator-false"
         "(begin-syntax (displayln \"NATIVE-SOURCE-FAILURE-BODY\") (raise #f))\n")))
    ;; Trace real compiler processes for an independent-source-first declaration.
    ;; Shared work has two consumers; its compilation should precede that leaf.
    (create-directory (path-expand "schedule" root))
    (write! "schedule/independent.ss" "(export independent) (def independent 0)\n")
    (write! "schedule/shared.ss" "(export shared) (def shared 40)\n")
    (write! "schedule/a.ss" "(import \"./shared.ss\") (export a) (def a (+ shared 1))\n")
    (write! "schedule/b.ss" "(import \"./shared.ss\") (export b) (def b (+ shared 2))\n")
    (def trace (path-expand "native-compile-order" root))
    (def (tracked name)
      (list gxc: name "-e"
        (call-with-output-string
          (lambda (port)
            (write `(call-with-output-file (list path: ,trace append: #t)
                      (lambda (output) (display ,name output) (newline output))) port)))))
    (native.make (map tracked '("independent" "shared" "a" "b"))
      srcdir: (path-expand "schedule" root)
      libdir: (path-expand "schedule-out" root)
      bindir: (path-expand "schedule-bin" root)
      prefix: "native-make-contract/schedule" parallelize: 1 verbose: #t)
    (require! (equal? (call-with-input-file trace read-line) "shared")
              "shared dependency was queued behind an unrelated leaf")
    (write! "consumer.ss" "(import \"./plain.ss\") (export result) (def result (+ answer 1))\n")
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
