#!/usr/bin/env gxi

(def (same-directory? actual expected)
  (or (equal? actual expected)
      (equal? actual (string-append expected "/"))))

(def (main command)
  (let ((expected-workspace
         (getenv "PROJECT_DEV_EXPECTED_WORKSPACE" #f))
        (actual-workspace (current-directory)))
    (unless expected-workspace
      (error "missing expected project-dev workspace"))
    (unless (equal? command "compile")
      (error "unexpected project-dev command" command))
    (unless (same-directory? actual-workspace expected-workspace)
      (error "project-dev launcher did not enter the workspace"
             actual-workspace
             expected-workspace))
    (displayln "project-dev-workspace=ok")))
