#!/usr/bin/env gxi
;;; -*- Gerbil -*-
;;; Contract validator for deterministic Gerbil-Bazel package receipt v1 instances.

(export main)

(import :gerbil/gambit :std/text/json)

(def +package-receipt-schema+ "gerbil-bazel.package-receipt.v1")

(def +package-fields+
  '("schema"
    "status"
    "libraryOutputRequired"
    "packageIdentity"
    "packageReference"
    "packageRevision"))

(def (contract-assert condition message . irritants)
  (unless condition (apply error message irritants)))

(def (read-json-file path)
  (call-with-input-file path read-json))

(def (exact-fields! value allowed label)
  (contract-assert
   (hash-table? value)
   "receipt value must be a JSON object"
   label)
  (hash-for-each
   (lambda (key _value)
     (contract-assert
      (member key allowed)
      "unexpected receipt field"
      label
      key))
   value))

(def (required-fields! value required label)
  (for-each
   (lambda (key)
     (contract-assert
      (hash-key? value key)
      "missing required receipt field"
      label
      key))
   required))

(def (non-empty-string? value)
  (and
   (string? value)
   (> (string-length value) 0)))

(def (validate-package-receipt! receipt path)
  (exact-fields! receipt +package-fields+ path)
  (required-fields! receipt +package-fields+ path)
  (contract-assert
   (string=?
    (hash-ref receipt "schema")
    +package-receipt-schema+)
   "invalid package receipt schema"
   path)
  (contract-assert
   (string=? (hash-ref receipt "status") "ok")
   "invalid package receipt status"
   path)
  (contract-assert
   (boolean? (hash-ref receipt "libraryOutputRequired"))
   "invalid package receipt library flag"
   path)
  (contract-assert
   (non-empty-string? (hash-ref receipt "packageIdentity"))
   "invalid package receipt package identity"
   path)
  (contract-assert
   (non-empty-string? (hash-ref receipt "packageReference"))
   "invalid package receipt package reference"
   path)
  (contract-assert
   (string? (hash-ref receipt "packageRevision"))
   "invalid package receipt package revision"
   path))

(def (validate-schema-owner! schema)
  (let* ((properties (hash-ref schema "properties"))
         (schema-property (hash-ref properties "schema")))
    (contract-assert
     (equal? (hash-ref schema "required") +package-fields+)
     "JSON Schema required fields drifted")
    (contract-assert
     (eq? (hash-ref schema "additionalProperties") #f)
     "JSON Schema must reject unknown top-level fields")
    (contract-assert
     (string=?
      (hash-ref schema-property "const")
      +package-receipt-schema+)
     "JSON Schema package receipt constant drifted")
    (for-each
     (lambda (key)
       (contract-assert
        (not (hash-key? properties key))
        "execution telemetry leaked into deterministic receipt schema"
        key))
     '("durationSeconds" "resourceBudget" "resourceGuard"))))

(def (main schema-path . receipt-paths)
  (contract-assert
   (pair? receipt-paths)
   "usage: validate_package_receipt_v1.ss SCHEMA RECEIPT [RECEIPT ...]")
  (validate-schema-owner! (read-json-file schema-path))
  (for-each
   (lambda (path)
     (validate-package-receipt! (read-json-file path) path))
   receipt-paths))
