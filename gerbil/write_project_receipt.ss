#!/usr/bin/env gxi
;;; -*- Gerbil -*-
;;; Native JSON writer for guarded Gerbil project receipts.

(export main)

(import :gerbil/gambit
        (only-in :std/text/json read-json json-object->string write-json-sort-keys?))

(def (read-json-file path)
  (call-with-input-file path read-json))

(def (read-json-string text)
  (let (port (open-input-string text))
    (read-json port)))

(def (optional-json-file path)
  (and (not (string=? path "-")) (read-json-file path)))

(def (main output duration-text library-required-text package-json revision-json
           guard-receipt-path build-receipt-path status)
  (let* ((duration-seconds (string->number duration-text))
       (library-required (string=? library-required-text "1"))
       (package-identity (read-json-string package-json))
       (package-revision (read-json-string revision-json))
       (guard-receipt (optional-json-file guard-receipt-path))
       (build-receipt (optional-json-file build-receipt-path))
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
  (parameterize ((write-json-sort-keys? #t))
    (call-with-output-file output
      (lambda (port)
        (display (json-object->string receipt) port)
        (newline port))))
    (exit 0)))
