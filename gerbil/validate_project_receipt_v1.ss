#!/usr/bin/env gxi
;;; -*- Gerbil -*-
;;; Contract validator for stable Gerbil-Bazel project receipt v1 instances.

(export main)

(import :gerbil/gambit :std/text/json)

(def +project-receipt-schema+ "gerbil-bazel.project-receipt.v1")
(def +resource-guard-schema+ "gerbil-bazel.resource-guard-receipt.v1")

(def +required-project-fields+
  '("schema"
    "status"
    "durationSeconds"
    "libraryOutputRequired"
    "packageIdentity"
    "packageRevision"))

(def +project-fields+
  (append
   +required-project-fields+
   '("resourceGuard" "dependencySourceResolutions" "buildReceipt")))

(def +dependency-source-resolution-fields+
  '("schema"
    "logicalPackage"
    "canonicalPackagePath"
    "canonicalUri"
    "expectedRevision"
    "observedRevision"
    "resolutionMode"
    "sourceSnapshotDigest"
    "sourceFileCount"
    "worktreeDirty"
    "outcome"))

(def +resource-guard-fields+
  '("kind"
    "schema"
    "version"
    "label"
    "outcome"
    "exitCode"
    "childExitCode"
    "logicalCpuCount"
    "runnableProcessCount"
    "systemMemoryBytes"
    "availableMemoryBytes"
    "rssHeadroomBytes"
    "maxRssBytes"
    "peakRssBytes"
    "processTreeRssAvailable"
    "elapsedMs"
    "timeoutMs"
    "admissionOutcome"
    "admissionAdvisories"
    "admissionReasons"))

(def (contract-assert condition message . irritants)
  (unless condition (apply error message irritants)))

(def (read-json-file path)
  (call-with-input-file path read-json))

(def (exact-fields! value allowed label)
  (contract-assert (hash-table? value) "receipt value must be a JSON object" label)
  (hash-for-each
   (lambda (key _value)
     (contract-assert (member key allowed) "unexpected receipt field" label key))
   value))

(def (required-fields! value required label)
  (for-each
   (lambda (key)
     (contract-assert (hash-key? value key) "missing required receipt field" label key))
   required))

(def (positive-integer? value)
  (and (exact-integer? value) (> value 0)))

(def (non-negative-integer? value)
  (and (exact-integer? value) (>= value 0)))

(def (false-or-non-negative-integer? value)
  (or (eq? value #f) (non-negative-integer? value)))

(def (string-list? value)
  (and (list? value) (andmap string? value)))

(def (non-empty-string? value)
  (and (string? value) (> (string-length value) 0)))

(def (lowercase-hex-string? value expected-length)
  (and
   (string? value)
   (= (string-length value) expected-length)
   (andmap
    (lambda (character)
      (member character (string->list "0123456789abcdef")))
    (string->list value))))

(def (source-digest? value)
  (and
   (string? value)
   (or
    (string=? value "")
    (lowercase-hex-string? value 40)
    (and
     (= (string-length value) 71)
     (string=? (substring value 0 7) "sha256:")
     (lowercase-hex-string? (substring value 7 71) 64)))))

(def (validate-dependency-source-resolution! resolution label)
  (exact-fields! resolution +dependency-source-resolution-fields+ label)
  (required-fields! resolution +dependency-source-resolution-fields+ label)
  (contract-assert
   (string=?
    (hash-ref resolution "schema")
    "gerbil-bazel.dependency-source-resolution-receipt.v1")
   "invalid dependency source-resolution schema"
   label)
  (for-each
   (lambda (key)
     (contract-assert
      (string? (hash-ref resolution key))
      "invalid dependency source-resolution string"
      label
      key))
   '("canonicalUri"
     "expectedRevision"
     "observedRevision"))
  (contract-assert
   (non-empty-string? (hash-ref resolution "logicalPackage"))
   "invalid logical dependency package"
   label)
  (contract-assert
   (string? (hash-ref resolution "canonicalPackagePath"))
   "invalid dependency canonical package path"
   label)
  (contract-assert
   (member
    (hash-ref resolution "resolutionMode")
    '("hermetic-archive" "identified-revision" "legacy-unique-source"))
   "invalid dependency source resolution mode"
   label)
  (contract-assert
   (source-digest? (hash-ref resolution "sourceSnapshotDigest"))
   "invalid dependency source snapshot digest"
   label)
  (contract-assert
   (positive-integer? (hash-ref resolution "sourceFileCount"))
   "invalid dependency source file count"
   label)
  (contract-assert
   (boolean? (hash-ref resolution "worktreeDirty"))
   "invalid dependency source worktree state"
   label)
  (contract-assert
   (string=? (hash-ref resolution "outcome") "resolved")
   "dependency source resolution did not resolve"
   label))

(def (validate-dependency-source-resolutions! resolutions label)
  (contract-assert
   (and (list? resolutions) (pair? resolutions))
   "dependency source resolutions must be a non-empty array"
   label)
  (let (seen (make-hash-table))
    (for-each
     (lambda (resolution)
       (validate-dependency-source-resolution! resolution label)
       (let (logical-package (hash-ref resolution "logicalPackage"))
         (contract-assert
          (not (hash-key? seen logical-package))
          "duplicate logical dependency source package"
          label
          logical-package)
         (hash-put! seen logical-package #t)))
     resolutions)))

(def (validate-resource-guard! guard label)
  (exact-fields!
   guard
   (append +resource-guard-fields+
           '("requestedBuildCoreCount"
             "effectiveBuildCoreCount"
             "availableMemoryBytes"
             "cgroupMemoryLimitBytes"
             "cgroupMemoryCurrentBytes"
             "cgroupMemoryAvailableBytes"
             "rssHeadroomBytes"
             "memoryPerCoreBytes"
             "memoryCoreLimit"
             "runnableProcessCount"
             "runnableProcessCountAvailable"
             "runnableCoreLimit"
             "runnableCoreLimitApplied"
             "processTreeRssAvailable"
             "processTreeMemoryMetric"
             "admissionOutcome"
             "admissionReasons"
             "admissionAdvisories"))
   label)
  (required-fields! guard +resource-guard-fields+ label)
  (contract-assert (string=? (hash-ref guard "kind") +resource-guard-schema+)
                   "invalid resource guard kind" label)
  (contract-assert (string=? (hash-ref guard "schema") +resource-guard-schema+)
                   "invalid resource guard schema" label)
  (contract-assert (= (hash-ref guard "version") 1)
                   "invalid resource guard version" label)
  (contract-assert (string? (hash-ref guard "label"))
                   "invalid resource guard label" label)
  (contract-assert
   (member (hash-ref guard "outcome")
           '("completed" "blocked-host-pressure" "rss-limit-exceeded" "timeout"))
   "invalid resource guard outcome" label)
  (contract-assert (non-negative-integer? (hash-ref guard "exitCode"))
                   "invalid resource guard exit code" label)
  (contract-assert
   (false-or-non-negative-integer? (hash-ref guard "childExitCode"))
   "invalid resource guard child exit code" label)
  (for-each
   (lambda (key)
     (contract-assert (positive-integer? (hash-ref guard key))
                      "invalid positive resource guard field" label key))
   '("logicalCpuCount"
     "runnableProcessCount"
     "systemMemoryBytes"
     "availableMemoryBytes"
     "rssHeadroomBytes"
     "maxRssBytes"))
  (for-each
   (lambda (key)
     (contract-assert (non-negative-integer? (hash-ref guard key))
                      "invalid non-negative resource guard field" label key))
   '("peakRssBytes" "elapsedMs"))
  (for-each
   (lambda (key)
     (when (hash-key? guard key)
       (contract-assert (non-negative-integer? (hash-ref guard key))
                        "invalid cgroup memory field" label key)))
   '("cgroupMemoryLimitBytes"
     "cgroupMemoryCurrentBytes"
     "cgroupMemoryAvailableBytes"))
  (contract-assert (boolean? (hash-ref guard "processTreeRssAvailable"))
                   "invalid process tree observability field" label)
  (when (hash-key? guard "processTreeMemoryMetric")
    (contract-assert
     (member (hash-ref guard "processTreeMemoryMetric") '("linux-pss" "rss"))
     "invalid process tree memory metric"
     label))
  (contract-assert
   (false-or-non-negative-integer? (hash-ref guard "timeoutMs"))
   "invalid resource guard timeout" label)
  (contract-assert
   (member (hash-ref guard "admissionOutcome")
           '("ready" "blocked-host-pressure"))
   "invalid resource guard admission outcome" label)
  (for-each
   (lambda (key)
     (contract-assert (string-list? (hash-ref guard key))
                      "invalid resource guard reason list" label key))
   '("admissionAdvisories" "admissionReasons")))

(def (validate-project-receipt! receipt path)
  (exact-fields! receipt +project-fields+ path)
  (required-fields! receipt +required-project-fields+ path)
  (contract-assert (string=? (hash-ref receipt "schema") +project-receipt-schema+)
                   "invalid project receipt schema" path)
  (contract-assert (string=? (hash-ref receipt "status") "ok")
                   "invalid project receipt status" path)
  (contract-assert (non-negative-integer? (hash-ref receipt "durationSeconds"))
                   "invalid project receipt duration" path)
  (contract-assert (boolean? (hash-ref receipt "libraryOutputRequired"))
                   "invalid project receipt library flag" path)
  (contract-assert (string? (hash-ref receipt "packageIdentity"))
                   "invalid project receipt package identity" path)
  (contract-assert (string? (hash-ref receipt "packageRevision"))
                   "invalid project receipt package revision" path)
  (when (hash-key? receipt "resourceGuard")
    (validate-resource-guard! (hash-ref receipt "resourceGuard") path))
  (when (hash-key? receipt "dependencySourceResolutions")
    (validate-dependency-source-resolutions!
     (hash-ref receipt "dependencySourceResolutions")
     path)))

(def (validate-schema-owner! schema)
  (let* ((properties (hash-ref schema "properties"))
         (schema-property (hash-ref properties "schema")))
    (contract-assert
     (equal? (hash-ref schema "required") +required-project-fields+)
     "JSON Schema required fields drifted")
    (contract-assert (eq? (hash-ref schema "additionalProperties") #f)
                     "JSON Schema must reject unknown top-level fields")
    (contract-assert (string=? (hash-ref schema-property "const")
                              +project-receipt-schema+)
                     "JSON Schema project receipt constant drifted")
    (for-each
     (lambda (key)
       (contract-assert (hash-key? properties key)
                        "JSON Schema extension field is missing" key))
     '("resourceGuard" "dependencySourceResolutions" "buildReceipt"))))

(def (main schema-path . receipt-paths)
  (contract-assert (pair? receipt-paths)
                   "usage: validate_project_receipt_v1.ss SCHEMA RECEIPT [RECEIPT ...]")
  (validate-schema-owner! (read-json-file schema-path))
  (for-each
   (lambda (path)
     (validate-project-receipt! (read-json-file path) path))
   receipt-paths))
