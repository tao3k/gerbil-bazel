;;; -*- Gerbil -*-

(export main)

(import :std/misc/plist)

(include "resource_policy.ss")

(def +configured-gxpkg+ {{GXPKG_SCHEME}})

(def (gxpkg-program)
  (or
   +configured-gxpkg+
   (string-append
    (executable-path)
    ".gxpkg")))

(def (apply-native-environment!)
{{ENVIRONMENT_SETTERS}})

(def (manifest-plist path)
  (call-with-input-file path read))

(def (string-value value fallback)
  (cond
   ((string? value) value)
   ((symbol? value) (symbol->string value))
   (else fallback)))

(def (dependency-repository dependency)
  (let (revision-index (string-index dependency #\@))
    (if revision-index
        (substring dependency 0 revision-index)
        dependency)))

(def (package-name-from-manifest manifest fallback)
  (string-value
   (pgetq package: (manifest-plist manifest) fallback)
   fallback))

(def (dependency-package gerbil-root dependency)
  (let* ((repository (dependency-repository dependency))
         (manifest
          (path-expand
           "gerbil.pkg"
           (path-expand
            repository
            (path-expand "pkg" gerbil-root)))))
    (if (file-exists? manifest)
        (package-name-from-manifest manifest repository)
        repository)))

(def (project-dependencies-ready? workspace gerbil-root)
  (let (manifest (path-expand "gerbil.pkg" workspace))
    (and
     (file-exists? manifest)
     (let (dependencies
           (pgetq depend: (manifest-plist manifest) '()))
       (and
        (pair? dependencies)
        (andmap
         (lambda (dependency)
           (file-exists?
            (path-expand
             (dependency-package gerbil-root dependency)
             (path-expand "lib" gerbil-root))))
         dependencies))))))

(def (display-install-failure phase status workspace gerbil-root)
  (display
   "gerbil-bazel install_dependencies failed: phase="
   (current-error-port))
  (display phase (current-error-port))
  (display " status=" (current-error-port))
  (display status (current-error-port))
  (display " workspace=" (current-error-port))
  (display workspace (current-error-port))
  (display " GERBIL_PATH=" (current-error-port))
  (display gerbil-root (current-error-port))
  (newline (current-error-port))
  (force-output (current-error-port)))

(def (main)
  (let* ((workspace
          (or
           (getenv "BUILD_WORKSPACE_DIRECTORY" #f)
           (error "BUILD_WORKSPACE_DIRECTORY is required")))
         (gerbil-root
          (or
           (getenv "GERBIL_PATH" #f)
           (path-expand ".gerbil" workspace)))
         (phase "initialize"))
    (with-catch
     (lambda (exception)
       (display-exception exception (current-error-port))
       (newline (current-error-port))
       (display-install-failure phase 70 workspace gerbil-root)
       (exit 70))
     (lambda ()
       (apply-native-environment!)
       (setenv "GERBIL_PATH" gerbil-root)
       (create-directory*
        (path-expand "pkg" gerbil-root))
       (set! phase "install")
       (let* ((timeout-seconds
               (let* ((raw
                       (getenv
                        "GERBIL_BAZEL_INSTALL_TIMEOUT_SECONDS"
                        "600"))
                      (value (string->number raw)))
                 (unless
                  (and
                   (exact-integer? value)
                   (>= value 0))
                  (error
                   "GERBIL_BAZEL_INSTALL_TIMEOUT_SECONDS must be a non-negative integer"
                   raw))
                 value))
              (guard-receipt-path
               (path-expand
                "install-resource-guard.receipt.json"
                (path-expand "pkg" gerbil-root)))
              (observation (host-observation))
              (budget
               (resolve-build-budget
                observation
                explicit-cores-env:
                "GERBIL_BAZEL_INSTALL_BUILD_CORES"
                memory-per-core-env:
                "GERBIL_BAZEL_INSTALL_MEMORY_PER_CORE_BYTES"))
              (_ (apply-build-budget! budget))
              (receipt
               (if
                (string=?
                 (hash-ref observation "admissionOutcome")
                 "ready")
                (run-guarded
                 "install-dependencies"
                 observation
                 (optional-timeout timeout-seconds)
                 (positive-real-from-env
                  "GERBIL_BAZEL_GUARD_SAMPLE_SECONDS"
                  +default-sample-seconds+)
     (list (gxpkg-program) "deps" "--install")
                 directory: workspace)
                (blocked-guard-receipt
                 observation
                 "install-dependencies"
                 (optional-timeout timeout-seconds))))
              (status (hash-ref receipt "exitCode")))
         (write-guard-receipt! guard-receipt-path receipt)
         (display
          "GERBIL_BAZEL_RESOURCE_BUDGET "
          (current-error-port))
         (display (receipt-json budget) (current-error-port))
         (newline (current-error-port))
         (cond
          ((= status 0)
           (exit 0))
          ((and
            (= status 71)
            (string=?
             (hash-ref receipt "outcome")
             "timeout")
            (project-dependencies-ready?
             workspace
             gerbil-root))
           (display
            "gerbil-bazel install_dependencies reached the Scheme guard deadline after project dependencies became ready; receipt="
            (current-error-port))
           (display guard-receipt-path (current-error-port))
           (newline (current-error-port))
           (exit 0))
          ((and
            (= status 71)
            (string=?
             (hash-ref receipt "outcome")
             "timeout"))
           (display
            "gerbil-bazel install_dependencies reached the Scheme guard deadline before project dependencies were ready; receipt="
            (current-error-port))
           (display guard-receipt-path (current-error-port))
           (newline (current-error-port))
           (exit 124))
          (else
           (display-install-failure
            phase
            status
            workspace
            gerbil-root)
           (exit status))))))))
