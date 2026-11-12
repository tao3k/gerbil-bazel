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
    ;; The authored header owns outputs even when the directory package differs.
    (def header-out (path-expand "header-out" root))
    (def header-spec '("explicit"))
    (def (build-header!)
      (native.make header-spec srcdir: root libdir: header-out
        prefix: "native-make-contract" parallelize: 1 verbose: #t))
    (build-header!)
    (def header-interface (path-expand "another/package/explicit.ssi" header-out))
    (def header-static (path-expand "static/another__package__explicit.scm" header-out))
    (require! (and (file-exists? header-interface) (file-exists? header-static))
              "explicit header products were not emitted at native identities")
    (def header-time (time->seconds (file-info-last-modification-time (file-info header-interface))))
    (def hot-header (call-with-output-string
                      (lambda (port) (parameterize ((current-output-port port)) (build-header!)))))
    (require! (not (string-contains hot-header "... compile "))
              "explicit header no-op recompiled")
    (require! (equal? header-time (time->seconds (file-info-last-modification-time (file-info header-interface))))
              "explicit header no-op replaced its product")
    (native.make-clean header-spec srcdir: root libdir: header-out prefix: "native-make-contract")
    (require! (not (or (file-exists? header-interface) (file-exists? header-static)))
              "standard clean retained explicit header products")
    (build-header!)
    ;; A native absolute source target must keep its authored module identity.
    (native.make (list (path-expand "explicit" root)) srcdir: root libdir: header-out
      prefix: "native-make-contract" parallelize: 1)
    (def header-result
      (run-process
        (list "env" (string-append "GERBIL_LOADPATH=" header-out)
              "gxi" "-:max-heap=2G,debug=q" "-e"
              "(import :another/package/explicit) (unless (= answer 42) (error \"header consumer mismatch\")) (displayln \"NATIVE-HEADER-CONSUMER-OK\")")
        stdout-redirection: #t coprocess: read-all-as-string))
    (require! (string-contains header-result "NATIVE-HEADER-CONSUMER-OK")
              "explicit header fresh compiled consumer failed")
    (write! "header-main.ss"
      "package: native-executable\n(export main) (def (main . args) (displayln \"NATIVE-HEADER-EXE-OK\"))\n")
    (def exe-bin (path-expand "header-bin" root))
    (def exe-spec '((exe: "header-main" bin: "header-main")))
    ;; Exercise the public declaration through the standard build entry too.
    (write! "header-build.ss"
      (call-with-output-string
        (lambda (port)
          (write '(import :std/build-script :std/source) port) (newline port)
          (write `(defbuild-script ',exe-spec libdir: ,header-out bindir: ,exe-bin) port)
          (newline port))))
    (def (exe-command command)
      (run-process
        (list "env" "GERBIL_BUILD_VERBOSE=1" "gxi" "-:max-heap=2G,debug=q"
              (path-expand "header-build.ss" root) command)
        stdout-redirection: #t coprocess: read-all-as-string))
    (def (build-exe!) (display (exe-command "compile")))
    (build-exe!)
    (def executable (path-expand "header-main" exe-bin))
    (def exe-static (path-expand "static/native-executable__header-main.scm" header-out))
    (require! (string-contains (run-process (list executable) stdout-redirection: #t
                               coprocess: read-all-as-string) "NATIVE-HEADER-EXE-OK")
              "explicit header executable failed")
    (def exe-time (time->seconds (file-info-last-modification-time (file-info executable))))
    (def hot-exe (call-with-output-string
                   (lambda (port) (parameterize ((current-output-port port)) (build-exe!)))))
    (require! (and (not (string-contains hot-exe "... compile "))
                  (equal? exe-time (time->seconds (file-info-last-modification-time
                                                   (file-info executable)))))
              "explicit header executable no-op rebuilt")
    (display (exe-command "clean"))
    (require! (not (or (file-exists? executable) (file-exists? exe-static)))
              "standard clean retained explicit header executable products")
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
