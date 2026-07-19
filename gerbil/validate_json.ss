#!/usr/bin/env gxi

(export main)

(import :std/text/json)

(def (main json-file)
  (call-with-input-file
   json-file
   (lambda (port)
     (let ((value (read-json port))
           (trailing-value (read-json port)))
       (when (eof-object? value)
         (error "expected one JSON value" json-file))
       (unless (eof-object? trailing-value)
         (error "expected exactly one JSON value" json-file))
       value))))
