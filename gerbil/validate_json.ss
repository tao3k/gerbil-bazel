#!/usr/bin/env gxi

(import :std/text/json)

(def arguments (cddr (command-line)))
(unless (= (length arguments) 1)
  (error "usage: validate_json.ss JSON_FILE" arguments))
(call-with-input-file
  (car arguments)
  (lambda (port)
    (let ((value (read-json port))
          (trailing-value (read-json port)))
      (when (eof-object? value)
        (error "expected one JSON value" (car arguments)))
      (unless (eof-object? trailing-value)
        (error "expected exactly one JSON value" (car arguments)))
      value)))
