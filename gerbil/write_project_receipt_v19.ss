#!/usr/bin/env gxi
;;; -*- Gerbil -*-
;;; Native JSON writer for guarded Gerbil project receipts.

(export main)

(import :gerbil/runtime/gambit
        (only-in :std/misc/ports read-file-lines)
        (only-in :std/encoding/json read-json string->json json->string))

(def (read-json-file path)
  (call-with-input-file path read-json))

(def (read-json-string text)
  (string->json text))

(def (optional-json-file path)
  (and (not (string=? path "-")) (read-json-file path)))

(def (json-files-from-manifest path)
  (map read-json-file (read-file-lines path)))

(def (main output duration-text library-required-text package-json revision-json
           guard-receipt-path build-receipt-path
           source-resolution-manifest-path status)
  (let* ((duration-seconds (string->number duration-text))
       (library-required (string=? library-required-text "1"))
       (package-identity (read-json-string package-json))
       (package-revision (read-json-string revision-json))
       (guard-receipt (optional-json-file guard-receipt-path))
       (build-receipt (optional-json-file build-receipt-path))
       (source-resolutions
        (json-files-from-manifest source-resolution-manifest-path))
       (receipt
        (hash
         ("schema" "gerbil-bazel.project-receipt.v1")
         ("status" status)
         ("durationSeconds" duration-seconds)
         ("libraryOutputRequired" library-required)
         ("packageIdentity" package-identity)
         ("packageRevision" package-revision)
         )))
  (when guard-receipt
    (hash-put! receipt "resourceGuard" guard-receipt))
  (when build-receipt
    (hash-put! receipt "buildReceipt" build-receipt))
  (when (pair? source-resolutions)
    (hash-put! receipt "dependencySourceResolutions" source-resolutions))
  (call-with-output-file output
    (lambda (port)
      (display (json->string receipt sort-keys: #t) port)
      (newline port)))
    (exit 0)))
