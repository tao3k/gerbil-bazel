#!/usr/bin/env gxi

(import :std/text/json)

(include "functional.ss")

(export main)

(def +aot-receipt-schema+ "gerbil-bazel.aot-receipt.v1")
(def +native-link-plan-schema+ "gerbil-bazel.native-link-plan.v1")

(def +aot-receipt-fields+
  '("schema"
    "module"
    "packageIdentity"
    "packageReference"
    "linkerName"
    "mainSymbol"
    "nativeAbiFingerprint"
    "explicitNativeSourceLabels"
    "linkLibraries"))

(def +native-link-plan-fields+
  '("schema"
    "moduleObjects"
    "linkObject"
    "linkSearchDirectories"
    "linkLibraries"))

(def (contract-assert condition message . irritants)
  (unless condition (apply error message irritants)))

(def (read-json-file path)
  (call-with-input-file path read-json))

(def (exact-fields! value allowed label)
  (contract-assert
   (hash-table? value)
   "AOT value must be a JSON object"
   label)
  (hash-for-each
   (lambda (key _value)
     (contract-assert
      (member key allowed)
      "unexpected AOT field"
      label
      key))
   value))

(def (required-fields! value required label)
  (for-each
   (lambda (key)
     (contract-assert
      (hash-key? value key)
      "missing required AOT field"
      label
      key))
   required))

(def (non-empty-string-list? value)
  (and
   (list? value)
   (pair? value)
   (andmap non-empty-string? value)))

(def (unique-list? value)
  (let loop ((rest value))
    (or
     (null? rest)
     (and
      (not (member (car rest) (cdr rest)))
      (loop (cdr rest))))))

(def (hex-string? value length)
  (and
   (string? value)
   (= (string-length value) length)
   (andmap
    (lambda (character)
      (or
       (and (char>=? character #\0) (char<=? character #\9))
       (and (char>=? character #\a) (char<=? character #\f))))
    (string->list value))))

(def (c-identifier? value)
  (and
   (non-empty-string? value)
   (let (characters (string->list value))
     (and
      (or
       (char-alphabetic? (car characters))
       (char=? (car characters) #\_))
      (andmap
       (lambda (character)
         (or
          (char-alphabetic? character)
          (char-numeric? character)
          (char=? character #\_)))
       characters)))))

(def (validate-schema-owner! schema fields constant label)
  (let* ((properties (hash-ref schema "properties"))
         (schema-property (hash-ref properties "schema")))
    (contract-assert
     (equal? (hash-ref schema "required") fields)
     "AOT JSON Schema required fields drifted"
     label)
    (contract-assert
     (eq? (hash-ref schema "additionalProperties") #f)
     "AOT JSON Schema must reject unknown top-level fields"
     label)
    (contract-assert
     (string=? (hash-ref schema-property "const") constant)
     "AOT JSON Schema constant drifted"
     label)))

(def (validate-link-libraries! value label)
  (contract-assert
   (non-empty-string-list? value)
   "AOT link libraries must be a non-empty string list"
   label))

(def (validate-plan! plan path)
  (exact-fields! plan +native-link-plan-fields+ path)
  (required-fields! plan +native-link-plan-fields+ path)
  (contract-assert
   (string=? (hash-ref plan "schema") +native-link-plan-schema+)
   "invalid native link plan schema"
   path)
  (let ((objects (hash-ref plan "moduleObjects"))
        (search-directories (hash-ref plan "linkSearchDirectories")))
    (contract-assert
     (and (non-empty-string-list? objects) (unique-list? objects))
     "invalid native link plan module objects"
     path)
    (contract-assert
     (and
      (non-empty-string-list? search-directories)
      (unique-list? search-directories))
     "invalid native link search directories"
     path))
  (contract-assert
   (non-empty-string? (hash-ref plan "linkObject"))
   "invalid native link object"
   path)
  (validate-link-libraries! (hash-ref plan "linkLibraries") path))

(def (validate-receipt! receipt path)
  (exact-fields! receipt +aot-receipt-fields+ path)
  (required-fields! receipt +aot-receipt-fields+ path)
  (contract-assert
   (string=? (hash-ref receipt "schema") +aot-receipt-schema+)
   "invalid AOT receipt schema"
   path)
  (for-each
   (lambda (field)
     (contract-assert
      (non-empty-string? (hash-ref receipt field))
      "invalid AOT receipt string field"
      path
      field))
   '("module" "packageIdentity" "packageReference"))
  (for-each
   (lambda (field)
     (contract-assert
      (c-identifier? (hash-ref receipt field))
      "invalid AOT receipt C identifier"
      path
      field))
   '("linkerName" "mainSymbol"))
  (contract-assert
   (hex-string? (hash-ref receipt "nativeAbiFingerprint") 40)
   "invalid AOT native ABI fingerprint"
   path)
  (let (source-labels (hash-ref receipt "explicitNativeSourceLabels"))
    (contract-assert
     (and
      (list? source-labels)
      (andmap non-empty-string? source-labels)
      (unique-list? source-labels))
     "invalid AOT native source labels"
     path))
  (validate-link-libraries! (hash-ref receipt "linkLibraries") path))

(def (main plan-schema-path receipt-schema-path plan-path receipt-path)
  (validate-schema-owner!
   (read-json-file plan-schema-path)
   +native-link-plan-fields+
   +native-link-plan-schema+
   plan-schema-path)
  (validate-schema-owner!
   (read-json-file receipt-schema-path)
   +aot-receipt-fields+
   +aot-receipt-schema+
   receipt-schema-path)
  (validate-plan! (read-json-file plan-path) plan-path)
  (validate-receipt! (read-json-file receipt-path) receipt-path))
