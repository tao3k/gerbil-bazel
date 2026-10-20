(import :std/encoding/json)

(def reference #f)
(for-each
 (lambda (iteration)
   (let* ((started (real-time))
          (result
           (call-with-input-file (getenv "PREGEXP_ATOMIC_STRINGS")
             (lambda (port)
               (let* ((buffer (make-string (* 4 1024 1024) #\space))
                      (count (read-substring buffer 0 (string-length buffer) port)))
                 (list count buffer (input-port-line port) (input-port-column port))))))
          (seconds (- (real-time) started)))
     (if reference
       (unless (equal? result reference) (error "capture contents or cursor changed"))
       (set! reference result))
     (displayln (json->string
                  (hash ("mode" "read-substring") ("iteration" iteration)
                        ("seconds" seconds) ("characters" (car result))
                        ("line" (caddr result)) ("column" (cadddr result))
                        ("exactPositionsMatch" #t))))
     (force-output)))
 '(0 1 2 3))
(displayln "OK")
