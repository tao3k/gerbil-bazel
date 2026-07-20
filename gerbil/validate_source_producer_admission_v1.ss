#!/usr/bin/env gxi
;;; -*- Gerbil -*-

(export main)

(import :gerbil/gambit :std/text/json)

(def +source-producer-admission-schema+
  "gerbil-bazel.source-producer-admission.v1")

(def +admission-fields+
  '("schema"
    "outcome"
    "cacheHit"
    "runnerExplicit"
    "configuredRunner"
    "selectedRunner"
    "sourceBuildRequired"
    "admitted"
    "reason"))

(def +required-admission-fields+ +admission-fields+)

(def (contract-assert condition message . irritants)
  (unless condition (apply error message irritants)))

(def (read-json-file path)
  (call-with-input-file path read-json))

(def (non-empty-string? value)
  (and (string? value) (> (string-length value) 0)))

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

(def (reason-conditional? value reason)
  (and (hash-table? value)
       (hash-key? value "if")
       (let ((condition (hash-ref value "if")))
         (and (hash-table? condition)
              (hash-key? condition "properties")
              (let ((properties (hash-ref condition "properties")))
                (and (hash-table? properties)
                     (hash-key? properties "reason")
                     (let ((reason-property (hash-ref properties "reason")))
                       (and (hash-table? reason-property)
                            (hash-key? reason-property "const")
                            (equal? (hash-ref reason-property "const") reason)))))))))

(def (find-reason-conditional conditionals reason)
  (cond
   ((null? conditionals) #f)
   ((reason-conditional? (car conditionals) reason) (car conditionals))
   (else (find-reason-conditional (cdr conditionals) reason))))

(def (conditional-property conditional field)
  (hash-ref
   (hash-ref
    (hash-ref conditional "then")
    "properties")
   field))

(def (assert-conditional-constants! schema reason expected)
  (let ((conditional (find-reason-conditional (hash-ref schema "allOf") reason)))
    (contract-assert conditional "JSON Schema reason conditional is missing" reason)
    (for-each
     (lambda (entry)
       (let ((property (conditional-property conditional (car entry))))
         (contract-assert (hash-key? property "const")
                          "JSON Schema conditional constant is missing"
                          reason
                          (car entry))
         (contract-assert (equal? (hash-ref property "const") (cdr entry))
                          "JSON Schema conditional constant drifted"
                          reason
                          (car entry))))
     expected)))

(def (validate-schema-owner! schema)
  (exact-fields!
   schema
   '("$schema" "$id" "title" "type" "additionalProperties" "required" "properties" "allOf")
   "source producer admission schema")
  (required-fields!
   schema
   '("$schema" "$id" "title" "type" "additionalProperties" "required" "properties" "allOf")
   "source producer admission schema")
  (let* ((properties (hash-ref schema "properties"))
         (schema-property (hash-ref properties "schema"))
         (reason-property (hash-ref properties "reason")))
    (contract-assert (equal? (hash-ref schema "required") +required-admission-fields+)
                     "JSON Schema required fields drifted")
    (contract-assert (eq? (hash-ref schema "additionalProperties") #f)
                     "JSON Schema must reject unknown top-level fields")
    (contract-assert (string=? (hash-ref schema-property "const")
                              +source-producer-admission-schema+)
                     "JSON Schema admission receipt constant drifted")
    (contract-assert
     (equal? (hash-ref reason-property "enum")
             '("complete-installation-cache-hit"
               "explicit-runner-cold-build"
               "implicit-default-runner-cold-miss"))
     "JSON Schema admission reasons drifted"))
  (assert-conditional-constants!
   schema
   "complete-installation-cache-hit"
   '(("outcome" . "admitted")
     ("cacheHit" . #t)
     ("sourceBuildRequired" . #f)
     ("admitted" . #t)))
  (assert-conditional-constants!
   schema
   "explicit-runner-cold-build"
   '(("outcome" . "admitted")
     ("cacheHit" . #f)
     ("runnerExplicit" . #t)
     ("sourceBuildRequired" . #t)
     ("admitted" . #t)))
  (assert-conditional-constants!
   schema
   "implicit-default-runner-cold-miss"
   '(("outcome" . "blocked")
     ("cacheHit" . #f)
     ("runnerExplicit" . #f)
     ("sourceBuildRequired" . #t)
     ("admitted" . #f))))

(def (validate-runner-selection! receipt path)
  (let ((runner-explicit (hash-ref receipt "runnerExplicit"))
        (configured-runner (hash-ref receipt "configuredRunner"))
        (selected-runner (hash-ref receipt "selectedRunner")))
    (contract-assert (boolean? runner-explicit)
                     "invalid runner explicitness field"
                     path)
    (contract-assert (non-empty-string? selected-runner)
                     "invalid selected runner"
                     path)
    (if runner-explicit
        (begin
          (contract-assert (non-empty-string? configured-runner)
                           "explicit runner must be configured"
                           path)
          (contract-assert (string=? configured-runner selected-runner)
                           "configured and selected runners differ"
                           path))
        (contract-assert (void? configured-runner)
                         "implicit runner must encode configuredRunner as JSON null"
                         path))))

(def (validate-admission-variant! receipt path)
  (let ((reason (hash-ref receipt "reason")))
    (cond
     ((string=? reason "complete-installation-cache-hit")
      (contract-assert (string=? (hash-ref receipt "outcome") "admitted")
                       "cache-hit admission outcome drifted" path)
      (contract-assert (eq? (hash-ref receipt "cacheHit") #t)
                       "cache-hit admission cache state drifted" path)
      (contract-assert (eq? (hash-ref receipt "sourceBuildRequired") #f)
                       "cache-hit admission source-build state drifted" path)
      (contract-assert (eq? (hash-ref receipt "admitted") #t)
                       "cache-hit admission decision drifted" path))
     ((string=? reason "explicit-runner-cold-build")
      (contract-assert (string=? (hash-ref receipt "outcome") "admitted")
                       "cold-build admission outcome drifted" path)
      (contract-assert (eq? (hash-ref receipt "cacheHit") #f)
                       "cold-build admission cache state drifted" path)
      (contract-assert (eq? (hash-ref receipt "runnerExplicit") #t)
                       "cold-build admission runner state drifted" path)
      (contract-assert (eq? (hash-ref receipt "sourceBuildRequired") #t)
                       "cold-build admission source-build state drifted" path)
      (contract-assert (eq? (hash-ref receipt "admitted") #t)
                       "cold-build admission decision drifted" path))
     ((string=? reason "implicit-default-runner-cold-miss")
      (contract-assert (string=? (hash-ref receipt "outcome") "blocked")
                       "cold-miss admission outcome drifted" path)
      (contract-assert (eq? (hash-ref receipt "cacheHit") #f)
                       "cold-miss admission cache state drifted" path)
      (contract-assert (eq? (hash-ref receipt "runnerExplicit") #f)
                       "cold-miss admission runner state drifted" path)
      (contract-assert (eq? (hash-ref receipt "sourceBuildRequired") #t)
                       "cold-miss admission source-build state drifted" path)
      (contract-assert (eq? (hash-ref receipt "admitted") #f)
                       "cold-miss admission decision drifted" path))
     (else (error "invalid source producer admission reason" path reason)))))

(def (validate-source-producer-admission! receipt path)
  (exact-fields! receipt +admission-fields+ path)
  (required-fields! receipt +required-admission-fields+ path)
  (contract-assert
   (string=? (hash-ref receipt "schema") +source-producer-admission-schema+)
   "invalid source producer admission schema"
   path)
  (contract-assert (member (hash-ref receipt "outcome") '("admitted" "blocked"))
                   "invalid source producer admission outcome"
                   path)
  (contract-assert (boolean? (hash-ref receipt "cacheHit"))
                   "invalid cache hit field"
                   path)
  (contract-assert (boolean? (hash-ref receipt "sourceBuildRequired"))
                   "invalid source build requirement field"
                   path)
  (contract-assert (boolean? (hash-ref receipt "admitted"))
                   "invalid admission decision field"
                   path)
  (contract-assert
   (member (hash-ref receipt "reason")
           '("complete-installation-cache-hit"
             "explicit-runner-cold-build"
             "implicit-default-runner-cold-miss"))
   "invalid source producer admission reason"
   path)
  (validate-runner-selection! receipt path)
  (validate-admission-variant! receipt path))

(def (main schema-path . receipt-paths)
  (contract-assert
   (pair? receipt-paths)
   "usage: validate_source_producer_admission_v1.ss SCHEMA RECEIPT [RECEIPT ...]")
  (validate-schema-owner! (read-json-file schema-path))
  (for-each
   (lambda (path)
     (validate-source-producer-admission! (read-json-file path) path))
   receipt-paths))
