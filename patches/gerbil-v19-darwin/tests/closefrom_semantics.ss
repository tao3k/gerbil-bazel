(import :std/os/fcntl :std/os/device)

(def (check label expected actual)
  (unless (equal? expected actual) (error label expected actual))
  (display "CASE-OK ") (displayln label) (force-output))

(def (child fds)
  (let* ((command
          (string-append
           "for fd in " (string-join (map number->string fds) " ")
           "; do if test -e /dev/fd/$fd; then printf LEAK; exit 19; fi; done; printf CLOSED"))
         (process (open-input-process
                   (list path: "sh" environment: '("PATH=/bin:/usr/bin")
                         arguments: (list "-c" command))))
         (output (read-line process))
         (status (process-status process)))
    (close-input-port process)
    (cons status output)))

(def (with-fds count minimum K)
  (let (fds [])
    (dynamic-wind
     (lambda ()
       (let loop ((n count))
         (when (> n 0)
           (let (fd (__fcntl2 1 F_DUPFD minimum))
             (unless (>= fd minimum) (error "FD allocation failed" fd))
             (set! fds (cons fd fds))
             (unless (zero? (bitwise-and (fcntl-getfd fd) FD_CLOEXEC))
               (error "fixture descriptor unexpectedly CLOEXEC" fd))
             (loop (- n 1))))))
     (lambda () (K fds))
     (lambda () (for-each __close-fd fds)))))

(with-fds 4 32
  (lambda (fds)
    (check "ordinary-descriptors-closed" '(0 . "CLOSED") (child fds))
    (check "ordinary-parent-descriptors-live" #t
           (andmap (lambda (fd) (>= (fcntl-getfd fd) 0)) fds))))
(with-fds 2 65536
  (lambda (fds)
    (check "sparse-high-descriptors-closed" '(0 . "CLOSED") (child fds))
    (check "sparse-parent-descriptors-live" #t
           (andmap (lambda (fd) (>= (fcntl-getfd fd) 0)) fds))))
(with-fds 4100 32
  (lambda (fds)
    (check "inventory-overflow-fallback-closes-all" '(0 . "CLOSED") (child fds))
    (check "overflow-parent-descriptors-live" #t
           (andmap (lambda (fd) (>= (fcntl-getfd fd) 0)) fds))))
(displayln "OK closefrom-semantics")
