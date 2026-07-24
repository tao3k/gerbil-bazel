#!/usr/bin/env gxi

(import :std/misc/ports
        :std/misc/process
        :std/text/json)

(include "functional.ss")

(export main)

(def +request-schema+ "gerbil-bazel.aot-request.v1")

(def (absolute-path path)
  (path-expand path))

(def (request-ref request key)
  (hash-ref request key))

(def (read-request request-path)
  (let (request
        (call-with-input-file
         (absolute-path request-path)
         read-json))
    (unless (equal? (request-ref request "schema") +request-schema+)
      (error "unsupported Gerbil AOT request schema"
             (request-ref request "schema")))
    request))

(def (copy-entry! entry)
  (let ((source (absolute-path (hash-ref entry "source")))
        (destination (absolute-path (hash-ref entry "destination"))))
    (unless (file-exists? source)
      (error "Gerbil AOT input does not exist" source))
    (create-directory* (path-directory destination))
    (copy-file source destination)))

(def (run-command! command directory log-port)
  (let ((argv (hash-ref command "argv"))
        (operation (hash-ref command "operation"))
        (status 0))
    (display "... " log-port)
    (display operation log-port)
    (newline log-port)
    (force-output log-port)
    (run-process
     argv
     stdin-redirection: #f
     stdout-redirection: #t
     stderr-redirection: #t
     coprocess:
     (lambda (process)
       (copy-port process log-port)
       (force-output log-port))
     check-status:
     (lambda (exit-status _settings)
       (set! status (normalized-exit-code exit-status)))
     directory: directory)
    (unless (zero? status)
      (error "Gerbil AOT compiler command failed" operation status))))

(def (ensure-output! path)
  (let (absolute (absolute-path path))
    (unless (file-exists? absolute)
      (error "Gerbil AOT compiler did not produce a declared output" absolute))))

(def (run-aot request)
  (let ((directory
         (absolute-path (request-ref request "workingDirectory")))
        (log-path
         (absolute-path (request-ref request "log"))))
    (create-directory* directory)
    (for-each copy-entry! (request-ref request "copies"))
    (call-with-output-file
     log-path
     (lambda (log-port)
       (for-each
        (lambda (command)
          (run-command! command directory log-port))
        (request-ref request "commands"))))
    (for-each ensure-output! (request-ref request "outputs"))))

(def (main request-path)
  (with-catch
   (lambda (failure)
     (display-exception failure (current-error-port))
     (newline (current-error-port))
     (exit 66))
   (lambda ()
     (run-aot (read-request request-path))
     (exit 0))))
