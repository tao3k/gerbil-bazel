#!/usr/bin/env gxi
;;; -*- Gerbil -*-
;;; Contract validator for non-canonical package execution telemetry v1.

(export main)

(import :gerbil/gambit :std/text/json)

(def +package-execution-telemetry-schema+
  "gerbil-bazel.package-execution-telemetry.v1")
(def +resource-guard-schema+
  "gerbil-bazel.resource-guard-receipt.v1")

(def +required-telemetry-fields+
  '("schema"
    "status"
    "durationSeconds"
    "packageIdentity"
    "packageReference"
    "packageRevision"
    "resourceBudget"))

(def +telemetry-fields+
  (append +required-telemetry-fields+ '("resourceGuard")))

(def +resource-budget-fields+
  '("schema"
    "decision"
    "selectedCores"
    "requestedCores"
    "configuredCores"
    "logicalCpuCount"
    "memoryPerCoreBytes"
    "memoryCoreLimit"
    "availableMemoryBytes"
    "maxRssBytes"))

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
  (contract-assert
   (hash-table? value)
   "telemetry value must be a JSON object"
   label)
  (hash-for-each
   (lambda (key _value)
     (contract-assert
      (member key allowed)
      "unexpected telemetry field"
      label
      key))
   value))

(def (required-fields! value required label)
  (for-each
   (lambda (key)
     (contract-assert
      (hash-key? value key)
      "missing required telemetry field"
      label
      key))
   required))

(def (positive-integer? value)
  (and (exact-integer? value) (> value 0)))

(def (non-negative-integer? value)
  (and (exact-integer? value) (>= value 0)))

(def (false-or-non-negative-integer? value)
  (or (eq? value #f) (non-negative-integer? value)))

(def (non-empty-string? value)
  (and
   (string? value)
   (> (string-length value) 0)))

(def (string-list? value)
  (and (list? value) (andmap string? value)))

(def (validate-resource-budget! budget label)
  (exact-fields! budget +resource-budget-fields+ label)
  (required-fields! budget +resource-budget-fields+ label)
  (contract-assert
   (string=?
    (hash-ref budget "schema")
    "gerbil-bazel.resource-budget.v1")
   "invalid resource budget schema"
   label)
  (contract-assert
   (member
    (hash-ref budget "decision")
    '("explicit"
      "explicit-memory-cap"
      "adaptive-configured"
      "adaptive-memory-cap"))
   "invalid resource budget decision"
   label)
  (for-each
   (lambda (key)
     (contract-assert
      (positive-integer? (hash-ref budget key))
      "invalid positive resource budget field"
      label
      key))
   '("selectedCores"
     "requestedCores"
     "configuredCores"
     "logicalCpuCount"
     "memoryPerCoreBytes"
     "memoryCoreLimit"
     "maxRssBytes"))
  (contract-assert
   (non-negative-integer?
    (hash-ref budget "availableMemoryBytes"))
   "invalid resource budget available memory"
   label))

(def (validate-resource-guard! guard label)
  (exact-fields! guard +resource-guard-fields+ label)
  (required-fields! guard +resource-guard-fields+ label)
  (contract-assert
   (string=? (hash-ref guard "kind") +resource-guard-schema+)
   "invalid resource guard kind"
   label)
  (contract-assert
   (string=? (hash-ref guard "schema") +resource-guard-schema+)
   "invalid resource guard schema"
   label)
  (contract-assert
   (= (hash-ref guard "version") 1)
   "invalid resource guard version"
   label)
  (contract-assert
   (string? (hash-ref guard "label"))
   "invalid resource guard label"
   label)
  (contract-assert
   (member
    (hash-ref guard "outcome")
    '("completed"
      "blocked-host-pressure"
      "rss-limit-exceeded"
      "timeout"))
   "invalid resource guard outcome"
   label)
  (contract-assert
   (non-negative-integer? (hash-ref guard "exitCode"))
   "invalid resource guard exit code"
   label)
  (contract-assert
   (false-or-non-negative-integer?
    (hash-ref guard "childExitCode"))
   "invalid resource guard child exit code"
   label)
  (for-each
   (lambda (key)
     (contract-assert
      (positive-integer? (hash-ref guard key))
      "invalid positive resource guard field"
      label
      key))
   '("logicalCpuCount"
     "runnableProcessCount"
     "systemMemoryBytes"
     "availableMemoryBytes"
     "rssHeadroomBytes"
     "maxRssBytes"))
  (for-each
   (lambda (key)
     (contract-assert
      (non-negative-integer? (hash-ref guard key))
      "invalid non-negative resource guard field"
      label
      key))
   '("peakRssBytes" "elapsedMs"))
  (contract-assert
   (boolean? (hash-ref guard "processTreeRssAvailable"))
   "invalid process tree observability field"
   label)
  (contract-assert
   (false-or-non-negative-integer?
    (hash-ref guard "timeoutMs"))
   "invalid resource guard timeout"
   label)
  (contract-assert
   (member
    (hash-ref guard "admissionOutcome")
    '("ready" "blocked-host-pressure"))
   "invalid resource guard admission outcome"
   label)
  (for-each
   (lambda (key)
     (contract-assert
      (string-list? (hash-ref guard key))
      "invalid resource guard reason list"
      label
      key))
   '("admissionAdvisories" "admissionReasons")))

(def (validate-telemetry! telemetry path)
  (exact-fields! telemetry +telemetry-fields+ path)
  (required-fields!
   telemetry
   +required-telemetry-fields+
   path)
  (contract-assert
   (string=?
    (hash-ref telemetry "schema")
    +package-execution-telemetry-schema+)
   "invalid package execution telemetry schema"
   path)
  (contract-assert
   (string=? (hash-ref telemetry "status") "ok")
   "invalid package execution telemetry status"
   path)
  (contract-assert
   (non-negative-integer?
    (hash-ref telemetry "durationSeconds"))
   "invalid package execution duration"
   path)
  (contract-assert
   (non-empty-string?
    (hash-ref telemetry "packageIdentity"))
   "invalid package execution package identity"
   path)
  (contract-assert
   (non-empty-string?
    (hash-ref telemetry "packageReference"))
   "invalid package execution package reference"
   path)
  (contract-assert
   (string? (hash-ref telemetry "packageRevision"))
   "invalid package execution package revision"
   path)
  (validate-resource-budget!
   (hash-ref telemetry "resourceBudget")
   path)
  (when (hash-key? telemetry "resourceGuard")
    (validate-resource-guard!
     (hash-ref telemetry "resourceGuard")
     path)))

(def (validate-schema-owner! schema)
  (let* ((properties (hash-ref schema "properties"))
         (schema-property (hash-ref properties "schema")))
    (contract-assert
     (equal?
      (hash-ref schema "required")
      +required-telemetry-fields+)
     "JSON Schema required fields drifted")
    (contract-assert
     (eq? (hash-ref schema "additionalProperties") #f)
     "JSON Schema must reject unknown top-level fields")
    (contract-assert
     (string=?
      (hash-ref schema-property "const")
      +package-execution-telemetry-schema+)
     "JSON Schema telemetry constant drifted")
    (contract-assert
     (hash-key? properties "resourceGuard")
     "JSON Schema resource guard extension is missing")))

(def (main schema-path . telemetry-paths)
  (contract-assert
   (pair? telemetry-paths)
   "usage: validate_package_execution_telemetry_v1.ss SCHEMA TELEMETRY [TELEMETRY ...]")
  (validate-schema-owner! (read-json-file schema-path))
  (for-each
   (lambda (path)
     (validate-telemetry! (read-json-file path) path))
   telemetry-paths))
