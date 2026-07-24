(include "resource_policy.ss")

(def +package-request-schema+
  "gerbil-bazel.package-request.v1")
(def +package-receipt-schema+
  "gerbil-bazel.package-receipt.v1")

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

(def (stage-sources! sources package-root)
  (let (destinations (make-hash-table))
    (for-each
     (lambda (entry)
       (let* ((source
               (absolute-path (hash-ref entry "source")))
              (relative
               (assert-safe-relative-path
                (hash-ref entry "destination")
                "staged package source path"))
              (previous (hash-get destinations relative))
              (destination
               (path-expand relative package-root)))
         (when previous
           (error
            "duplicate staged package source path"
            relative
            previous
            source))
         (hash-put! destinations relative source)
         (copy-source! source destination)))
     sources)))

(def (path-list value)
  (if (list? value) value '()))

(def (materialize-gxpkg-dependencies! dependencies package-root)
  (let (package-directory
        (path-expand ".gerbil/pkg" package-root))
    (ensure-empty-directory! package-directory)
    (for-each
     (lambda (dependency)
       (let* ((reference
               (hash-ref dependency "reference"))
              (source
               (absolute-path
                (hash-ref dependency "manifest")))
              (destination
               (path-expand
                (string-append reference ".manifest")
                package-directory)))
         (validate-gxpkg-dependency-manifest! source reference)
         (copy-source! source destination)))
     dependencies)))

(def (read-single-datum path description)
  (call-with-input-file
   path
   (lambda (input)
     (let* ((datum (read input))
            (_datum
             (request-assert
              (not (eof-object? datum))
              (string-append description " is empty")
              path))
            (trailing (read input))
            (_trailing
             (request-assert
              (eof-object? trailing)
              (string-append description " must contain exactly one datum")
              path)))
       datum))))

(def (validate-gxpkg-dependency-manifest! path reference)
  (let* ((manifest
          (read-single-datum path "dependency gxpkg manifest"))
         (_manifest
          (request-assert
           (and
            (list? manifest)
            (pair? manifest))
           "dependency gxpkg manifest must be a nonempty association list"
           path))
         (entry (car manifest))
         (_entry
          (request-assert
           (and
            (pair? entry)
            (equal? (car entry) reference)
            (non-empty-string? (cdr entry)))
           "dependency gxpkg manifest identity does not match its reference"
           path)))
    manifest))

(def (dependency-loadpath package-root dependency-root dependency-roots)
  (let* ((package-library
          (path-expand ".gerbil/lib" package-root))
         (roots
          (map
           (lambda (root)
             (let (library
                   (path-expand
                    ".gerbil/lib"
                    (absolute-path root)))
               (unless (file-exists? library)
                 (error
                  "Gerbil package dependency library root is missing"
                  library))
               library))
           dependency-roots)))
    (string-join
     (cons package-library (append roots (list dependency-root)))
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
           (error "required Gerbil package tool is missing" program)))
         (link (path-expand name tool-bin)))
    (when (file-exists? link)
      (delete-file-or-directory link))
    (create-symbolic-link target link)))

(def (configure-tool-environment! request package-root)
  (let* ((tools (request-ref request "tools"))
         (tool-bin (path-expand ".gerbil-tool-bin" package-root))
         (gerbil-path (path-expand ".gerbil" package-root))
         (dependency-marker
          (absolute-path
           (request-ref request "dependencyRootMarker")))
         (dependency-root (path-directory dependency-marker))
         (dependency-roots
          (path-list
           (request-ref request "packageDependencyRoots"))))
    (create-directory* (path-expand "lib" gerbil-path))
    (materialize-gxpkg-dependencies!
     (request-ref request "packageDependencies")
     package-root)
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
      package-root
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
                (request-ref request "packageLabel")
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
                (request-ref request "packageLabel")
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
       "Gerbil package typed failure receipts follow"
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

(def (package-receipt
      request
      duration-seconds
      library-required?
      budget
      guard-receipt)
  (let (receipt
        (hash
         ("schema" +package-receipt-schema+)
         ("status" "ok")
         ("durationSeconds" duration-seconds)
         ("libraryOutputRequired" library-required?)
         ("packageIdentity"
          (request-ref request "packageIdentity"))
         ("packageReference"
          (request-ref request "packageReference"))
         ("packageRevision"
          (request-ref request "packageRevision"))
         ("resourceBudget" budget)))
    (when guard-receipt
      (hash-put! receipt "resourceGuard" guard-receipt))
    receipt))

(def (read-local-version-manifest path)
  (let* ((form
          (read-single-datum path "upstream gxpkg manifest.ss"))
         (_form
          (request-assert
           (and
            (list? form)
            (= (length form) 3)
            (eq? (car form) 'def)
            (eq? (cadr form) 'version-manifest))
           "upstream gxpkg manifest.ss has an invalid definition"
           path))
         (quoted (caddr form))
         (_quoted
          (request-assert
           (and
            (list? quoted)
            (= (length quoted) 2)
            (eq? (car quoted) 'quote)
            (list? (cadr quoted))
            (pair? (cadr quoted)))
           "upstream gxpkg manifest.ss has an invalid quoted manifest"
           path)))
    (cadr quoted)))

(def (write-gxpkg-manifest! request package-source-root)
  (let* ((generated-path
          (path-expand "manifest.ss" package-source-root))
         (_generated
          (request-assert
           (file-exists? generated-path)
           "upstream gxpkg build produced no manifest.ss"
           generated-path))
         (generated
          (read-local-version-manifest generated-path))
         (revision
          (request-ref request "packageRevision"))
         (canonical
          (cons
           (cons
            (request-ref request "packageReference")
            (if
             (> (string-length revision) 0)
             revision
             "unknown"))
           (cdr generated)))
         (output-path
          (absolute-path
           (request-ref request "gxpkgManifest"))))
    (create-directory* (path-directory output-path))
    (call-with-output-file
     [path: output-path create: 'maybe truncate: #t]
     (lambda (output)
       (pretty-print canonical output)))
    (read-single-datum output-path "generated dependency gxpkg manifest")
    canonical))

(def +package-request-fields+
  '("schema"
    "args"
    "manifest"
    "dependencyRootMarker"
    "gxpkgManifest"
    "log"
    "packageDependencies"
    "packageIdentity"
    "packageReference"
    "packageRevision"
    "processGuard"
    "processGuardTimeoutSeconds"
    "packageDependencyRoots"
    "packageLabel"
    "packageRoot"
    "receipt"
    "requireLibraryOutput"
    "sources"
    "tools"))

(def +package-dependency-fields+
  '("manifest" "reference"))

(def +package-source-fields+ '("destination" "source"))
(def +package-tool-fields+ '("as" "cc" "gxc" "gxi" "gxpkg" "ld"))

(def (request-assert condition message . irritants)
  (unless condition
    (apply error message irritants)))

(def (request-exact-fields! value allowed label)
  (request-assert
   (hash-table? value)
   "Gerbil package request value must be a JSON object"
   label)
  (hash-for-each
   (lambda (key _value)
     (request-assert
      (member key allowed)
      "unexpected Gerbil package request field"
      label
      key))
   value))

(def (request-required-fields! value required label)
  (for-each
   (lambda (key)
     (request-assert
      (hash-key? value key)
      "missing Gerbil package request field"
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

(def (authorized-package-root-envelope package-root)
  (let ((test-root (getenv "TEST_TMPDIR" #f))
        (bazel-output-root
         (lexical-absolute-path "bazel-out")))
    (cond
     ((and
       test-root
       (lexically-contained? package-root test-root))
      (lexical-absolute-path test-root))
     ((lexically-contained?
       package-root
       bazel-output-root)
      bazel-output-root)
     (else #f))))

(def (assert-package-input-outside! path package-root label)
  (request-assert
   (not (path-contained? path package-root))
   "Gerbil package input would be deleted with package root"
   label
   path
   package-root))

(def (validate-package-root!
      package-root
      gxpkg-manifest-path
      log-path
      receipt-path)
  (let* ((lexical-root (lexical-absolute-path package-root))
         (authorized-envelope
          (authorized-package-root-envelope lexical-root))
         (_authorized
          (request-assert
           authorized-envelope
           "Gerbil package root is outside the Bazel or test output envelope"
           package-root))
         (relative-root
          (subpath? lexical-root authorized-envelope))
         (_strict-descendant
          (request-assert
           (and
            relative-root
            (> (string-length relative-root) 0))
           "Gerbil package root must be a strict output-envelope descendant"
           package-root))
         (physical-envelope
          (normalized-absolute-path authorized-envelope))
         (expected-physical-root
          (path-simplify
           (path-expand
            relative-root
            physical-envelope)))
         (absolute-root
          (normalized-absolute-path lexical-root))
         (absolute-gxpkg-manifest
          (normalized-absolute-path gxpkg-manifest-path))
         (absolute-log (normalized-absolute-path log-path))
         (absolute-receipt (normalized-absolute-path receipt-path))
         (working-directory
          (normalized-absolute-path (current-directory))))
    (request-assert
     (string=?
      (strip-trailing-directory-separators absolute-root)
      (strip-trailing-directory-separators
       expected-physical-root))
     "Gerbil package root crosses a symlink below its authorized output envelope"
     package-root
     absolute-root
     expected-physical-root)
    (request-assert
     (not (path-contained? working-directory absolute-root))
     "Gerbil package root cannot contain the working directory"
     package-root)
    (request-assert
     (not
      (path-contained? absolute-gxpkg-manifest absolute-root))
     "Gerbil gxpkg manifest cannot be inside the destructively staged package root"
     gxpkg-manifest-path
     package-root)
    (request-assert
     (not (path-contained? absolute-log absolute-root))
     "Gerbil package log cannot be inside the destructively staged package root"
     log-path
     package-root)
    (request-assert
     (not (path-contained? absolute-receipt absolute-root))
     "Gerbil package receipt cannot be inside the destructively staged package root"
     receipt-path
     package-root)
    (request-assert
     (and
      (not (string=? absolute-gxpkg-manifest absolute-log))
      (not (string=? absolute-gxpkg-manifest absolute-receipt)))
     "Gerbil gxpkg manifest, log, and receipt paths must be distinct"
     gxpkg-manifest-path
     log-path
     receipt-path)
    (request-assert
     (not (string=? absolute-log absolute-receipt))
     "Gerbil package log and receipt paths must be distinct"
     log-path
     receipt-path)
    lexical-root))

(def (validate-package-sources! sources package-root manifest)
  (request-assert
   (and
    (list? sources)
    (pair? sources))
   "Gerbil package sources must be a nonempty list")
  (let ((destinations
         (map
          (lambda (source-entry)
            (request-exact-fields!
             source-entry
             +package-source-fields+
             "source")
            (request-required-fields!
             source-entry
             +package-source-fields+
             "source")
            (let ((source (request-ref source-entry "source"))
                  (destination
                   (request-ref source-entry "destination")))
              (request-assert
               (non-empty-string? source)
               "Gerbil package source path must be a nonempty string"
               source)
              (assert-safe-relative-path
               destination
               "Gerbil package source destination")
              (request-assert
               (file-exists? (normalized-absolute-path source))
               "Gerbil package source does not exist"
               source)
              (assert-package-input-outside!
               source
               package-root
               "source")
              destination))
          sources)))
    (request-assert
     (unique-items? destinations)
     "duplicate Gerbil package source destination")
    (request-assert
     (member manifest destinations)
     "Gerbil package manifest is not staged by the request"
     manifest)))

(def (validate-package-tools! tools package-root)
  (request-exact-fields! tools +package-tool-fields+ "tools")
  (request-required-fields! tools +package-tool-fields+ "tools")
  (for-each
   (lambda (key)
     (let* ((program (request-ref tools key))
            (resolved
             (and
              (non-empty-string? program)
              (find-program program))))
       (request-assert
        (and resolved (file-exists? resolved))
        "Gerbil package tool does not exist"
        key
        program)
       (assert-package-input-outside!
        resolved
        package-root
        key)))
   +package-tool-fields+))

(def (validate-package-dependency-roots! roots package-root)
  (request-assert
   (list-of? non-empty-string? roots)
   "Gerbil package dependency roots must be a list of nonempty strings")
  (request-assert
   (unique-items? roots)
   "Gerbil package dependency roots must be unique")
  (for-each
   (lambda (root)
     (request-assert
      (file-exists? (normalized-absolute-path root))
      "Gerbil package dependency root does not exist"
      root)
     (assert-package-input-outside!
      root
      package-root
      "package dependency root"))
   roots))

(def (validate-package-dependencies! dependencies package-root)
  (request-assert
   (list? dependencies)
   "Gerbil package dependencies must be a list")
  (let ((references
         (map
          (lambda (dependency)
            (request-exact-fields!
             dependency
             +package-dependency-fields+
             "package dependency")
            (request-required-fields!
             dependency
             +package-dependency-fields+
             "package dependency")
            (let ((manifest
                   (request-ref dependency "manifest"))
                  (reference
                   (request-ref dependency "reference")))
              (request-assert
               (non-empty-string? manifest)
               "Gerbil dependency manifest path must be nonempty")
              (assert-safe-relative-path
               reference
               "Gerbil dependency reference")
              (request-assert
               (file-exists?
                (normalized-absolute-path manifest))
               "Gerbil dependency gxpkg manifest does not exist"
               manifest)
              (assert-package-input-outside!
               manifest
               package-root
               "dependency gxpkg manifest")
              reference))
          dependencies)))
    (request-assert
     (unique-items? references)
     "Gerbil package dependency references must be unique")))

(def (validate-package-request! request request-path)
  (request-exact-fields!
   request
   +package-request-fields+
   request-path)
  (request-required-fields!
   request
   +package-request-fields+
   request-path)
  (request-assert
   (and
    (string? (request-ref request "schema"))
    (string=?
     (request-ref request "schema")
     +package-request-schema+))
   "unsupported Gerbil package request"
   request-path)
  (for-each
   (lambda (key)
     (request-assert
      (non-empty-string? (request-ref request key))
      "Gerbil package request field must be a nonempty string"
      key))
  '("manifest"
    "dependencyRootMarker"
    "gxpkgManifest"
    "log"
    "packageIdentity"
    "packageLabel"
    "packageReference"
    "packageRoot"
    "receipt"))
  (for-each
   (lambda (key)
     (request-assert
      (string? (request-ref request key))
      "Gerbil package request field must be a string"
      key))
  '("packageRevision"))
  (assert-safe-relative-path
   (request-ref request "packageIdentity")
   "Gerbil package identity")
  (assert-safe-relative-path
   (request-ref request "packageReference")
   "Gerbil package reference")
  (request-assert
   (list-of? string? (request-ref request "args"))
   "Gerbil package args must be a list of strings")
  (request-assert
   (boolean? (request-ref request "processGuard"))
   "Gerbil package processGuard must be a boolean")
  (request-assert
   (non-negative-exact-integer?
    (request-ref request "processGuardTimeoutSeconds"))
   "Gerbil package processGuardTimeoutSeconds must be a nonnegative integer")
  (request-assert
   (boolean? (request-ref request "requireLibraryOutput"))
   "Gerbil package requireLibraryOutput must be a boolean")
  (let* ((package-root
         (validate-package-root!
           (request-ref request "packageRoot")
           (request-ref request "gxpkgManifest")
           (request-ref request "log")
           (request-ref request "receipt")))
         (manifest
          (assert-safe-relative-path
           (request-ref request "manifest")
           "Gerbil package manifest"))
         (dependency-root-marker
          (request-ref request "dependencyRootMarker")))
    (request-assert
     (file-exists?
      (normalized-absolute-path dependency-root-marker))
     "Gerbil dependency root marker does not exist"
     dependency-root-marker)
    (assert-package-input-outside!
     dependency-root-marker
     package-root
     "dependency root marker")
    (validate-package-sources!
     (request-ref request "sources")
     package-root
     manifest)
    (validate-package-tools!
     (request-ref request "tools")
     package-root)
    (validate-package-dependency-roots!
     (request-ref request "packageDependencyRoots")
     package-root)
    (validate-package-dependencies!
     (request-ref request "packageDependencies")
     package-root))
  request)

(def (read-request request-path)
  (let (request
        (call-with-input-file
         (absolute-path request-path)
         read-json))
    (validate-package-request! request request-path)))

(def (run-package request)
  (let* ((package-root
          (absolute-path
           (request-ref request "packageRoot")))
         (receipt-path
          (absolute-path
           (request-ref request "receipt")))
         (log-path
          (absolute-path
           (request-ref request "log")))
         (manifest
          (assert-safe-relative-path
           (request-ref request "manifest")
           "staged package manifest path"))
         (failure-receipt-dir
          (string-append log-path ".failure-receipts"))
         (started (now-seconds)))
    (ensure-empty-directory! package-root)
    (stage-sources!
     (request-ref request "sources")
     package-root)
    (let* ((staged-manifest
            (path-expand manifest package-root))
           (package-source-root
            (path-directory staged-manifest))
           (internal-builder
            (path-expand "build.ss" package-source-root)))
      (unless (and
               (file-exists? staged-manifest)
               (string=? (path-strip-directory staged-manifest) "gerbil.pkg"))
        (error "staged gerbil.pkg is missing" manifest))
      (unless (file-exists? internal-builder)
        (error "staged package is missing internal upstream builder"
               package-source-root))
      (ensure-empty-directory! failure-receipt-dir)
      (setenv
       "GERBIL_BAZEL_FAILURE_RECEIPT_DIR"
       failure-receipt-dir)
      (let* ((tool-bin
              (configure-tool-environment! request package-root))
             (observation (host-observation))
             (budget
              (resolve-build-budget observation))
             (_ (apply-build-budget! budget))
             (argv
              (cons
               (find-program
                (hash-ref
                 (request-ref request "tools")
                 "gxpkg"))
               (cons
                "build"
                (request-ref request "args"))))
             (execution
              (execute-build!
               request
               observation
               argv
               package-source-root
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
              "Gerbil package build failed with exit "
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
                (path-expand ".gerbil/lib" package-root)))
          (when
           (and
            library-required?
            (not
             (directory-contains-regular-file?
              library-root)))
            (error
             "Gerbil package build produced no library files"
             library-root))
          (write-gxpkg-manifest! request package-source-root)
          (delete-tree! (path-expand ".gerbil/pkg" package-root))
          (let* ((duration-seconds
                  (inexact->exact
                   (round (- (now-seconds) started))))
                 (receipt
                  (package-receipt
                   request
                   duration-seconds
                   library-required?
                   budget
                   guard-receipt)))
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
     (run-package (read-request request-path))
     (exit 0))))
