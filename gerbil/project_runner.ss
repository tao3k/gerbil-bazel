(include "resource_policy.ss")

(def +project-request-schema+
  "gerbil-bazel.project-request.v1")
(def +project-receipt-schema+
  "gerbil-bazel.project-receipt.v1")

(def (request-ref request key)
  (hash-ref request key))

(def (absolute-path path)
  (ensure-absolute-path path))

(def (safe-relative-path? path)
  (and
   (string? path)
   (> (string-length path) 0)
   (not (path-absolute? path))
   (let loop ((segments (string-split path #\/)))
     (or
      (null? segments)
      (and
       (> (string-length (car segments)) 0)
       (not (member (car segments) '("." "..")))
       (loop (cdr segments)))))))

(def (assert-safe-relative-path path description)
  (unless (safe-relative-path? path)
    (error
     (string-append "invalid " description)
     path))
  path)

(def (directory-entries path)
  (let (directory
        (open-directory
         (list path: path ignore-hidden: #f)))
    (dynamic-wind
        void
        (lambda ()
          (let loop ((entries '()))
            (let (entry (read directory))
              (if (eof-object? entry)
                  (reverse entries)
                  (loop
                   (if (member entry '("." ".."))
                       entries
                       (cons entry entries)))))))
        (lambda ()
          (close-port directory)))))

(def (symbolic-link? path)
  (let (info
        (with-catch
         (lambda (_error) #f)
         (lambda () (file-info path #f))))
    (and info (eq? (file-info-type info) 'symbolic-link))))

(def (delete-tree! path)
  (when (file-exists? path)
    (if (and
         (not (symbolic-link? path))
         (eq? (file-type path) 'directory))
        (begin
          (for-each
           (lambda (name)
             (delete-tree! (path-expand name path)))
           (directory-entries path))
          (delete-directory path))
        (delete-file path))))

(def (ensure-empty-directory! path)
  (when (file-exists? path)
    (delete-tree! path))
  (create-directory* path))

(def (copy-source! source destination)
  (create-directory* (path-directory destination))
  (copy-file source destination))

(def (stage-sources! sources project-root)
  (let (destinations (make-hash-table))
    (for-each
     (lambda (entry)
       (let* ((source
               (absolute-path (hash-ref entry "source")))
              (relative
               (assert-safe-relative-path
                (hash-ref entry "destination")
                "staged project source path"))
              (previous (hash-get destinations relative))
              (destination
               (path-expand relative project-root)))
         (when previous
           (error
            "duplicate staged project source path"
            relative
            previous
            source))
         (hash-put! destinations relative source)
         (copy-source! source destination)))
     sources)))

(def (path-list value)
  (if (list? value) value '()))

(def (dependency-loadpath project-root dependency-root dependency-roots)
  (let* ((project-library
          (path-expand ".gerbil/lib" project-root))
         (roots
          (map
           (lambda (root)
             (let (library
                   (path-expand
                    ".gerbil/lib"
                    (absolute-path root)))
               (unless (file-exists? library)
                 (error
                  "Gerbil project dependency library root is missing"
                  library))
               library))
           dependency-roots)))
    (string-join
     (cons project-library (append roots (list dependency-root)))
     ":")))

(def (find-program program)
  (cond
   ((path-absolute? program) program)
   ((file-exists? program) (absolute-path program))
   (else
    (let loop
        ((directories
          (string-split (getenv "PATH" "") #\:)))
      (and
       (pair? directories)
       (let (candidate
             (path-expand program (car directories)))
         (if (file-exists? candidate)
             candidate
             (loop (cdr directories)))))))))

(def (link-tool! tool-bin name program)
  (let* ((target
          (or
           (find-program program)
           (error "required Gerbil project tool is missing" program)))
         (link (path-expand name tool-bin)))
    (when (file-exists? link)
      (delete-file-or-directory link))
    (create-symbolic-link target link)))

(def (configure-tool-environment! request project-root)
  (let* ((tools (request-ref request "tools"))
         (tool-bin (path-expand ".gerbil-tool-bin" project-root))
         (gerbil-path (path-expand ".gerbil" project-root))
         (dependency-marker
          (absolute-path
           (request-ref request "dependencyRootMarker")))
         (dependency-root (path-directory dependency-marker))
         (dependency-roots
          (path-list
           (request-ref request "projectDependencyRoots"))))
    (create-directory* (path-expand "lib" gerbil-path))
    (create-directory* tool-bin)
    (link-tool! tool-bin "gxi" (hash-ref tools "gxi"))
    (link-tool! tool-bin "gxc" (hash-ref tools "gxc"))
    (link-tool! tool-bin "gxpkg" (hash-ref tools "gxpkg"))
    (link-tool! tool-bin "cc" (hash-ref tools "cc"))
    (link-tool! tool-bin "as" (hash-ref tools "as"))
    (link-tool! tool-bin "ld" (hash-ref tools "ld"))
    (setenv "CC" (find-program (hash-ref tools "cc")))
    (setenv "GERBIL_PATH" gerbil-path)
    (setenv
     "GERBIL_LOADPATH"
     (dependency-loadpath
      project-root
      dependency-root
      dependency-roots))
    (setenv
     "PATH"
     (string-append
      tool-bin
      ":"
      (getenv "PATH" "")))
    tool-bin))

(def (run-child argv directory log-path)
  (let (status 0)
    (run-process
     argv
     stdin-redirection: #f
     stdout-redirection: #t
     stderr-redirection: #t
     coprocess:
     (lambda (process)
       (call-with-output-file
        log-path
        (lambda (output)
          (copy-port process output))))
     check-status:
     (lambda (exit-status _settings)
       (set! status (normalized-exit-code exit-status)))
     directory: directory)
    status))

(def (execute-build!
      request
      observation
      argv
      build-source-root
      log-path)
  (let* ((process-guard?
          (request-ref request "processGuard"))
         (declared-timeout
          (request-ref request "processGuardTimeoutSeconds"))
         (timeout-seconds
          (optional-timeout declared-timeout)))
    (if process-guard?
        (let (receipt
              (if
               (string=?
                (hash-ref observation "admissionOutcome")
                "ready")
               (run-guarded
                (request-ref request "projectLabel")
                observation
                timeout-seconds
                (positive-real-from-env
                 "GERBIL_BAZEL_GUARD_SAMPLE_SECONDS"
                 +default-sample-seconds+)
                argv
                directory: build-source-root
                output-path: log-path)
               (blocked-guard-receipt
                observation
                (request-ref request "projectLabel")
                timeout-seconds)))
          (cons (hash-ref receipt "exitCode") receipt))
        (cons
         (run-child argv build-source-root log-path)
         #f))))

(def (directory-contains-regular-file? root)
  (let loop ((pending (list root)))
    (and
     (pair? pending)
     (let* ((path (car pending))
            (rest (cdr pending))
            (type
             (with-catch
              (lambda (_error) #f)
              (lambda () (file-type path)))))
       (cond
        ((eq? type 'regular) #t)
        ((eq? type 'directory)
         (loop
          (append
            (map
            (lambda (name) (path-expand name path))
            (directory-entries path))
           rest)))
        (else (loop rest)))))))

(def (emit-lines! lines port)
  (for-each
   (lambda (line)
     (display line port)
     (newline port))
   lines)
  (force-output port))

(def (display-line! value port)
  (display value port)
  (newline port))

(def (typed-compiler-receipt-line? line)
  (or
   (string-contains
    line
    "\"kind\":\"gerbil-bazel.compiler-failure-receipt.v1\"")
   (string-contains
    line
    "\"kind\":\"gerbil-bazel.compiler-input-receipt.v1\"")))

(def (emit-failure-receipts! failure-receipt-dir log-path)
  (let* ((receipt-files
          (if (file-exists? failure-receipt-dir)
              (map
               (lambda (name)
                 (path-expand name failure-receipt-dir))
               (directory-files failure-receipt-dir))
              '()))
         (receipt-lines
          (if
           (null? receipt-files)
           '()
           (apply
            append
            (map
             (lambda (path)
               (if (eq? (file-type path) 'regular)
                   (read-file-lines path)
                   '()))
             receipt-files))))
         (log-lines
          (if (file-exists? log-path)
              (read-file-lines log-path)
              '()))
         (embedded-lines
          (filter
           (lambda (line)
             (string-contains
              line
              "GERBIL_BAZEL_COMPILER_"))
           log-lines)))
    (when (or (pair? receipt-lines) (pair? embedded-lines))
      (display-line!
       "Gerbil project typed failure receipts follow"
       (current-error-port)))
    (for-each
     (lambda (line)
       (display
       (if
         (typed-compiler-receipt-line? line)
         "GERBIL_BAZEL_COMPILER_RECEIPT "
         "GERBIL_BAZEL_COMPILER_RECEIPT_INVALID ")
        (current-error-port))
       (display-line! line (current-error-port)))
     receipt-lines)
    (emit-lines! embedded-lines (current-error-port))
    log-lines))

(def (last-prefixed-json log-path prefix)
  (and
   (> (string-length prefix) 0)
   (let loop
       ((lines (read-file-lines log-path))
        (selected #f))
     (if (null? lines)
         selected
         (let (line (car lines))
           (loop
            (cdr lines)
            (if (string-prefix? prefix line)
                (substring
                 line
                 (string-length prefix)
                 (string-length line))
                selected)))))))

(def (parse-json-string text description)
  (with-catch
   (lambda (error)
     (error
      (string-append "invalid " description)
      text
      error))
   (lambda ()
     (read-json (open-input-string text)))))

(def (boolean-from-env name fallback)
  (let (raw (getenv name #f))
    (cond
     ((not raw) fallback)
     ((string=? raw "0") #f)
     ((string=? raw "1") #t)
     (else
      (error
       (string-append name " must be 0 or 1")
       raw)))))

(def (project-receipt
      request
      duration-seconds
      library-required?
      budget
      guard-receipt
      build-receipt)
  (let (receipt
        (hash
         ("schema" +project-receipt-schema+)
         ("status" "ok")
         ("durationSeconds" duration-seconds)
         ("libraryOutputRequired" library-required?)
         ("packageIdentity"
          (request-ref request "packageIdentity"))
         ("packageRevision"
          (request-ref request "packageRevision"))
         ("resourceBudget" budget)))
    (when guard-receipt
      (hash-put! receipt "resourceGuard" guard-receipt))
    (when build-receipt
      (hash-put! receipt "buildReceipt" build-receipt))
    receipt))

(def +project-request-fields+
  '("schema"
    "args"
    "buildScript"
    "dependencyRootMarker"
    "log"
    "packageIdentity"
    "packageRevision"
    "processGuard"
    "processGuardTimeoutSeconds"
    "projectDependencyRoots"
    "projectLabel"
    "projectRoot"
    "receipt"
    "receiptLinePrefix"
    "requireLibraryOutput"
    "sources"
    "tools"))

(def +project-source-fields+ '("destination" "source"))
(def +project-tool-fields+ '("as" "cc" "gxc" "gxi" "gxpkg" "ld"))

(def (request-assert condition message . irritants)
  (unless condition
    (apply error message irritants)))

(def (request-exact-fields! value allowed label)
  (request-assert
   (hash-table? value)
   "Gerbil project request value must be a JSON object"
   label)
  (hash-for-each
   (lambda (key _value)
     (request-assert
      (member key allowed)
      "unexpected Gerbil project request field"
      label
      key))
   value))

(def (request-required-fields! value required label)
  (for-each
   (lambda (key)
     (request-assert
      (hash-key? value key)
      "missing Gerbil project request field"
      label
      key))
   required))

(def (lexical-absolute-path path)
  (path-simplify (absolute-path path)))

(def (canonical-path-envelope path)
  (let loop
      ((candidate (lexical-absolute-path path))
       (suffix '()))
    (if
     (file-exists? candidate)
     (let append-components
         ((result (path-normalize candidate))
          (remaining suffix))
       (if
        (null? remaining)
        (path-simplify result)
        (append-components
         (path-expand (car remaining) result)
         (cdr remaining))))
     (let (parent (path-directory candidate))
       (request-assert
        (not (string=? parent candidate))
        "cannot resolve a physical path envelope"
        path)
       (loop
        parent
        (cons
         (path-strip-directory candidate)
         suffix))))))

(def (normalized-absolute-path path)
  (canonical-path-envelope path))

(def (strip-trailing-directory-separators path)
  (let loop ((value path))
    (if
     (and
      (> (string-length value) 1)
      (string-suffix? "/" value))
     (loop
      (substring
       value
       0
       (- (string-length value) 1)))
     value)))

(def (lexically-contained? path base)
  (if
   (subpath?
    (lexical-absolute-path path)
    (lexical-absolute-path base))
   #t
   #f))

(def (path-contained? path base)
  (if
   (subpath?
    (normalized-absolute-path path)
    (normalized-absolute-path base))
   #t
   #f))

(def (authorized-project-root-envelope project-root)
  (let ((test-root (getenv "TEST_TMPDIR" #f))
        (bazel-output-root
         (lexical-absolute-path "bazel-out")))
    (cond
     ((and
       test-root
       (lexically-contained? project-root test-root))
      (lexical-absolute-path test-root))
     ((lexically-contained?
       project-root
       bazel-output-root)
      bazel-output-root)
     (else #f))))

(def (assert-project-input-outside! path project-root label)
  (request-assert
   (not (path-contained? path project-root))
   "Gerbil project input would be deleted with project root"
   label
   path
   project-root))

(def (validate-project-root! project-root log-path receipt-path)
  (let* ((lexical-root (lexical-absolute-path project-root))
         (authorized-envelope
          (authorized-project-root-envelope lexical-root))
         (_authorized
          (request-assert
           authorized-envelope
           "Gerbil project root is outside the Bazel or test output envelope"
           project-root))
         (relative-root
          (subpath? lexical-root authorized-envelope))
         (_strict-descendant
          (request-assert
           (and
            relative-root
            (> (string-length relative-root) 0))
           "Gerbil project root must be a strict output-envelope descendant"
           project-root))
         (physical-envelope
          (normalized-absolute-path authorized-envelope))
         (expected-physical-root
          (path-simplify
           (path-expand
            relative-root
            physical-envelope)))
         (absolute-root
          (normalized-absolute-path lexical-root))
         (absolute-log (normalized-absolute-path log-path))
         (absolute-receipt (normalized-absolute-path receipt-path))
         (working-directory
          (normalized-absolute-path (current-directory))))
    (request-assert
     (string=?
      (strip-trailing-directory-separators absolute-root)
      (strip-trailing-directory-separators
       expected-physical-root))
     "Gerbil project root crosses a symlink below its authorized output envelope"
     project-root
     absolute-root
     expected-physical-root)
    (request-assert
     (not (path-contained? working-directory absolute-root))
     "Gerbil project root cannot contain the working directory"
     project-root)
    (request-assert
     (not (path-contained? absolute-log absolute-root))
     "Gerbil project log cannot be inside the destructively staged project root"
     log-path
     project-root)
    (request-assert
     (not (path-contained? absolute-receipt absolute-root))
     "Gerbil project receipt cannot be inside the destructively staged project root"
     receipt-path
     project-root)
    (request-assert
     (not (string=? absolute-log absolute-receipt))
     "Gerbil project log and receipt paths must be distinct"
     log-path
     receipt-path)
    lexical-root))

(def (validate-project-sources! sources project-root build-script)
  (request-assert
   (and
    (list? sources)
    (pair? sources))
   "Gerbil project sources must be a nonempty list")
  (let ((destinations
         (map
          (lambda (source-entry)
            (request-exact-fields!
             source-entry
             +project-source-fields+
             "source")
            (request-required-fields!
             source-entry
             +project-source-fields+
             "source")
            (let ((source (request-ref source-entry "source"))
                  (destination
                   (request-ref source-entry "destination")))
              (request-assert
               (non-empty-string? source)
               "Gerbil project source path must be a nonempty string"
               source)
              (assert-safe-relative-path
               destination
               "Gerbil project source destination")
              (request-assert
               (file-exists? (normalized-absolute-path source))
               "Gerbil project source does not exist"
               source)
              (assert-project-input-outside!
               source
               project-root
               "source")
              destination))
          sources)))
    (request-assert
     (unique-items? destinations)
     "duplicate Gerbil project source destination")
    (request-assert
     (member build-script destinations)
     "Gerbil build script is not staged by the request"
     build-script)))

(def (validate-project-tools! tools project-root)
  (request-exact-fields! tools +project-tool-fields+ "tools")
  (request-required-fields! tools +project-tool-fields+ "tools")
  (for-each
   (lambda (key)
     (let* ((program (request-ref tools key))
            (resolved
             (and
              (non-empty-string? program)
              (find-program program))))
       (request-assert
        (and resolved (file-exists? resolved))
        "Gerbil project tool does not exist"
        key
        program)
       (assert-project-input-outside!
        resolved
        project-root
        key)))
   +project-tool-fields+))

(def (validate-project-dependencies! roots project-root)
  (request-assert
   (list-of? non-empty-string? roots)
   "Gerbil project dependency roots must be a list of nonempty strings")
  (request-assert
   (unique-items? roots)
   "Gerbil project dependency roots must be unique")
  (for-each
   (lambda (root)
     (request-assert
      (file-exists? (normalized-absolute-path root))
      "Gerbil project dependency root does not exist"
      root)
     (assert-project-input-outside!
      root
      project-root
      "project dependency root"))
   roots))

(def (validate-project-request! request request-path)
  (request-exact-fields!
   request
   +project-request-fields+
   request-path)
  (request-required-fields!
   request
   +project-request-fields+
   request-path)
  (request-assert
   (and
    (string? (request-ref request "schema"))
    (string=?
     (request-ref request "schema")
     +project-request-schema+))
   "unsupported Gerbil project request"
   request-path)
  (for-each
   (lambda (key)
     (request-assert
      (non-empty-string? (request-ref request key))
      "Gerbil project request field must be a nonempty string"
      key))
   '("buildScript"
     "dependencyRootMarker"
     "log"
     "projectLabel"
     "projectRoot"
     "receipt"))
  (for-each
   (lambda (key)
     (request-assert
      (string? (request-ref request key))
      "Gerbil project request field must be a string"
      key))
   '("packageIdentity" "packageRevision" "receiptLinePrefix"))
  (request-assert
   (list-of? string? (request-ref request "args"))
   "Gerbil project args must be a list of strings")
  (request-assert
   (boolean? (request-ref request "processGuard"))
   "Gerbil project processGuard must be a boolean")
  (request-assert
   (non-negative-exact-integer?
    (request-ref request "processGuardTimeoutSeconds"))
   "Gerbil project processGuardTimeoutSeconds must be a nonnegative integer")
  (request-assert
   (boolean? (request-ref request "requireLibraryOutput"))
   "Gerbil project requireLibraryOutput must be a boolean")
  (let* ((project-root
          (validate-project-root!
           (request-ref request "projectRoot")
           (request-ref request "log")
           (request-ref request "receipt")))
         (build-script
          (assert-safe-relative-path
           (request-ref request "buildScript")
           "Gerbil build script"))
         (dependency-root-marker
          (request-ref request "dependencyRootMarker")))
    (request-assert
     (file-exists?
      (normalized-absolute-path dependency-root-marker))
     "Gerbil dependency root marker does not exist"
     dependency-root-marker)
    (assert-project-input-outside!
     dependency-root-marker
     project-root
     "dependency root marker")
    (validate-project-sources!
     (request-ref request "sources")
     project-root
     build-script)
    (validate-project-tools!
     (request-ref request "tools")
     project-root)
    (validate-project-dependencies!
     (request-ref request "projectDependencyRoots")
     project-root))
  request)

(def (read-request request-path)
  (let (request
        (call-with-input-file
         (absolute-path request-path)
         read-json))
    (validate-project-request! request request-path)))

(def (run-project request)
  (let* ((project-root
          (absolute-path
           (request-ref request "projectRoot")))
         (receipt-path
          (absolute-path
           (request-ref request "receipt")))
         (log-path
          (absolute-path
           (request-ref request "log")))
         (build-script
          (assert-safe-relative-path
           (request-ref request "buildScript")
           "staged build script path"))
         (failure-receipt-dir
          (string-append log-path ".failure-receipts"))
         (started (now-seconds)))
    (ensure-empty-directory! project-root)
    (stage-sources!
     (request-ref request "sources")
     project-root)
    (let* ((staged-build-script
            (path-expand build-script project-root))
           (build-source-root
            (path-directory staged-build-script)))
      (unless (file-exists? staged-build-script)
        (error "staged build script is missing" build-script))
      (ensure-empty-directory! failure-receipt-dir)
      (setenv
       "GERBIL_BAZEL_FAILURE_RECEIPT_DIR"
       failure-receipt-dir)
      (let* ((tool-bin
              (configure-tool-environment! request project-root))
             (observation (host-observation))
             (budget
              (resolve-build-budget observation))
             (_ (apply-build-budget! budget))
             (argv
              (cons
               (find-program
                (hash-ref
                 (request-ref request "tools")
                 "gxi"))
               (cons
                staged-build-script
                (request-ref request "args"))))
             (execution
              (execute-build!
               request
               observation
               argv
               build-source-root
               log-path))
             (status (car execution))
             (guard-receipt (cdr execution)))
        (delete-tree! tool-bin)
        (when (not (= status 0))
          (let (log-lines
                (emit-failure-receipts!
                 failure-receipt-dir
                 log-path))
            (display-line!
             (string-append
              "Gerbil project build failed with exit "
              (number->string status)
              "; final log follows")
             (current-error-port))
            (emit-lines!
             (tail-lines log-lines 200)
             (current-error-port)))
          (exit status))
        (delete-tree! failure-receipt-dir)
        (let* ((library-required?
                (boolean-from-env
                 "GERBIL_BAZEL_REQUIRE_LIBRARY_OUTPUT"
                 (request-ref request "requireLibraryOutput")))
               (library-root
                (path-expand ".gerbil/lib" project-root)))
          (when
           (and
            library-required?
            (not
             (directory-contains-regular-file?
              library-root)))
            (error
             "Gerbil project build produced no library files"
             library-root))
          (let* ((prefix
                  (request-ref request "receiptLinePrefix"))
                 (build-receipt-text
                  (last-prefixed-json log-path prefix))
                 (build-receipt
                  (and
                   build-receipt-text
                   (parse-json-string
                    build-receipt-text
                    "prefixed build receipt")))
                 (duration-seconds
                  (inexact->exact
                   (round (- (now-seconds) started))))
                 (receipt
                  (project-receipt
                   request
                   duration-seconds
                   library-required?
                   budget
                   guard-receipt
                   build-receipt)))
            (when
             (and
              (> (string-length prefix) 0)
              (not build-receipt-text))
              (error
               "Gerbil project build completed without receipt prefix"
               prefix))
            (write-json-file! receipt-path receipt)
            (call-with-input-file receipt-path read-json)
            receipt))))))

(def (main request-path)
  (with-catch
   (lambda (error)
     (display-exception error (current-error-port))
     (newline (current-error-port))
     (exit 66))
   (lambda ()
     (run-project (read-request request-path))
     (exit 0))))
