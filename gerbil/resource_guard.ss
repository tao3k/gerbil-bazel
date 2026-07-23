#!/usr/bin/env gxi
;;; -*- Gerbil -*-
;;; Scheme-owned host admission, process-tree RSS, and deadline guard.

(export main)

(import :gerbil/gambit
        (only-in :std/misc/process run-process)
        (only-in :std/srfi/13 string-trim-both string-tokenize)
        (only-in :std/text/json json-object->string write-json-sort-keys?))

(def +resource-guard-schema+ "gerbil-bazel.resource-guard-receipt.v1")
(def +minimum-max-rss-bytes+ (* 768 1024 1024))
(def +headroom-share-denominator+ 16)
(def +runnable-limit-per-cpu+ 2)
(def +default-sample-seconds+ 0.25)

(def (now-seconds)
  (time->seconds (current-time)))

(def (normalized-exit-code status)
  (cond
   ((< status 0) 1)
   ((> status 255) (quotient status 256))
   (else status)))

(def (run-captured argv)
  (with-catch
   (lambda (_error) (cons 126 ""))
   (lambda ()
     (let (status 0)
       (let (output
             (run-process
              argv
              stderr-redirection: #t
              check-status:
              (lambda (exit-status _settings)
                (set! status exit-status))))
         (cons (normalized-exit-code status) output))))))

(def (command-positive-integer argv)
  (with-catch
   (lambda (_error) #f)
   (lambda ()
     (let* ((result (run-captured argv))
            (value (and (= (car result) 0)
                        (string->number (string-trim-both (cdr result))))))
       (and (exact-integer? value) (> value 0) value)))))

(def (positive-integer-from-env name fallback)
  (let* ((raw (getenv name #f))
         (value (and raw (string->number raw))))
    (if (and (exact-integer? value) (> value 0)) value fallback)))

(def (positive-real-from-env name fallback)
  (let* ((raw (getenv name #f))
         (value (and raw (string->number raw))))
    (if (and (real? value) (> value 0)) value fallback)))

(def (optional-timeout declared-timeout)
  (let* ((raw (getenv "GERBIL_BAZEL_GUARD_TIMEOUT_SECONDS" #f))
         (value (and raw (string->number raw))))
    (cond
     ((and raw (exact-integer? value) (= value 0)) #f)
     ((and raw (exact-integer? value) (> value 0)) value)
     (raw (error "GERBIL_BAZEL_GUARD_TIMEOUT_SECONDS must be a non-negative integer" raw))
     ((> declared-timeout 0) declared-timeout)
     (else #f))))

(def (logical-cpu-count)
  (positive-integer-from-env
   "GERBIL_BAZEL_GUARD_LOGICAL_CPU_COUNT"
   (max 1 (##cpu-count))))

(def (runnable-process-count)
  (or (positive-integer-from-env
       "GERBIL_BAZEL_GUARD_RUNNABLE_PROCESSES"
       #f)
      (command-positive-integer
       (list "sh" "-c"
             "ps -axo state= 2>/dev/null | awk '$1 ~ /^R/ {n++} END {print n+0}'"))
      1))

(def (system-memory-bytes)
  (or (positive-integer-from-env
       "GERBIL_BAZEL_GUARD_SYSTEM_MEMORY_BYTES"
       #f)
      (command-positive-integer (list "sysctl" "-n" "hw.memsize"))
      (let ((pages (command-positive-integer (list "getconf" "_PHYS_PAGES")))
            (page-size (command-positive-integer (list "getconf" "PAGE_SIZE"))))
        (and pages page-size (* pages page-size)))
      (* 8 +minimum-max-rss-bytes+)))

(def (linux-available-memory-bytes)
  (command-positive-integer
   (list "sh" "-c"
         "if test -r /proc/meminfo; then awk '/^MemAvailable:/ {printf \"%.0f\\n\", $2 * 1024; exit}' /proc/meminfo; fi")))

(def (darwin-available-memory-percent)
  (command-positive-integer
   (list "sh" "-c"
         "if command -v memory_pressure >/dev/null 2>&1; then memory_pressure -Q 2>/dev/null | awk '/System-wide memory free percentage:/ {gsub(/%/, \"\", $NF); print $NF; exit}'; fi")))

(def (available-memory-bytes total-memory)
  (or (positive-integer-from-env
       "GERBIL_BAZEL_GUARD_AVAILABLE_MEMORY_BYTES"
       #f)
      (linux-available-memory-bytes)
      (let (percent (darwin-available-memory-percent))
        (and percent (quotient (* total-memory percent) 100)))
      total-memory))

(def (default-headroom-bytes total-memory)
  (max +minimum-max-rss-bytes+
       (quotient total-memory +headroom-share-denominator+)))

(def (live-process-table-result)
  (run-captured (list "ps" "-axo" "pid=,ppid=,rss=")))

(def (process-table-result)
  (cond
   ((getenv "GERBIL_BAZEL_GUARD_FORCE_PROCESS_TABLE_UNAVAILABLE" #f)
    (cons 126 ""))
   ((getenv "GERBIL_BAZEL_GUARD_PROCESS_TABLE_SNAPSHOT" #f)
    => (lambda (snapshot) (cons 0 snapshot)))
   (else
    (live-process-table-result))))

(def (host-observation)
  (let* ((total-memory (system-memory-bytes))
         (available-memory (available-memory-bytes total-memory))
         (headroom
          (positive-integer-from-env
           "GERBIL_BAZEL_GUARD_RSS_HEADROOM_BYTES"
           (default-headroom-bytes total-memory)))
         (available-max-rss
          (max 1 (- available-memory headroom)))
         (explicit-max-rss
          (positive-integer-from-env
           "GERBIL_BAZEL_GUARD_MAX_RSS_BYTES"
           #f))
         (max-rss
          (if explicit-max-rss
              (min explicit-max-rss available-max-rss)
              available-max-rss))
         (logical-cpus (logical-cpu-count))
         (runnable (runnable-process-count))
         (process-table-probe (process-table-result))
         (process-tree-rss-available? (= (car process-table-probe) 0))
         (advisories
          (if (> runnable (* logical-cpus +runnable-limit-per-cpu+))
              '(runnable-saturation)
              '()))
         (reasons
          (append
           (if (< available-memory (+ headroom +minimum-max-rss-bytes+))
               '(insufficient-memory-headroom)
               '())
           (if process-tree-rss-available?
               '()
               '(process-tree-rss-unavailable)))))
    (hash
     ("logicalCpuCount" logical-cpus)
     ("runnableProcessCount" runnable)
     ("systemMemoryBytes" total-memory)
     ("availableMemoryBytes" available-memory)
     ("rssHeadroomBytes" headroom)
     ("maxRssBytes" max-rss)
     ("processTreeRssAvailable" process-tree-rss-available?)
     ("admissionOutcome" (if (null? reasons) "ready" "blocked-host-pressure"))
     ("admissionAdvisories" (map symbol->string advisories))
     ("admissionReasons" (map symbol->string reasons)))))

(def (process-row line)
  (let (tokens (string-tokenize line))
    (and (= (length tokens) 3)
         (let ((pid (string->number (car tokens)))
               (ppid (string->number (cadr tokens)))
               (rss-kib (string->number (caddr tokens))))
           (and pid ppid rss-kib (list pid ppid (* rss-kib 1024)))))))

(def (process-table)
  (let (result (process-table-result))
    (if (= (car result) 0)
        (filter-map process-row (string-split (cdr result) #\newline))
        '())))

(def (live-process-table)
  (let (result (live-process-table-result))
    (if (= (car result) 0)
      (filter-map process-row (string-split (cdr result) #\newline))
      '())))

(def (process-tree-pids root-pid rows)
  (let expand ((known (list root-pid)))
    (let lp ((rest rows) (next known) (changed? #f))
      (if (null? rest)
          (if changed? (expand next) next)
          (let* ((row (car rest))
                 (pid (car row))
                 (ppid (cadr row)))
            (if (and (member ppid next) (not (member pid next)))
                (lp (cdr rest) (cons pid next) #t)
                (lp (cdr rest) next changed?)))))))

(def (process-tree-rss-bytes pid)
  (let* ((rows (process-table))
         (tree-pids (process-tree-pids pid rows)))
    (foldl
     (lambda (row total)
       (if (member (car row) tree-pids) (+ total (caddr row)) total))
     0
     rows)))

(def (signal-process! signal pid)
  (= (car (run-captured
           (list "kill" signal (number->string pid))))
     0))

(def (new-process-tree-pids observed known)
  (filter-map
   (lambda (observed-pid)
     (and (not (member observed-pid known)) observed-pid))
   observed))

(def (freeze-process-tree-pids! pid)
  ;; Freeze the root before discovery so it cannot create new direct children
  ;; while the live descendant closure converges.
  (signal-process! "-STOP" pid)
  (let loop ((known (list pid)))
    (let* ((tree-pids (process-tree-pids pid (live-process-table)))
           (new-pids (new-process-tree-pids tree-pids known)))
      ;; Descendants may have forked before STOP was delivered. Freeze every
      ;; newly observed PID and rescan until the live closure is stable.
      (for-each
       (lambda (new-pid)
         (signal-process! "-STOP" new-pid))
       new-pids)
      (if (null? new-pids)
        tree-pids
        (loop tree-pids)))))

(def (terminate-process-tree! pid)
  (let (tree-pids (freeze-process-tree-pids! pid))
    ;; process-tree-pids conses newly discovered descendants ahead of their
    ;; ancestors, so termination is descendant-first with the root last.
    (for-each
     (lambda (tree-pid)
       (signal-process! "-KILL" tree-pid))
     tree-pids)))

(def (guard-receipt label observation outcome exit-code child-exit-code
                    peak-rss-bytes elapsed-ms timeout-seconds)
  (hash
   ("kind" +resource-guard-schema+)
   ("schema" +resource-guard-schema+)
   ("version" 1)
   ("label" label)
   ("outcome" (symbol->string outcome))
   ("exitCode" exit-code)
   ("childExitCode" child-exit-code)
   ("logicalCpuCount" (hash-ref observation "logicalCpuCount"))
   ("runnableProcessCount" (hash-ref observation "runnableProcessCount"))
   ("systemMemoryBytes" (hash-ref observation "systemMemoryBytes"))
   ("availableMemoryBytes" (hash-ref observation "availableMemoryBytes"))
   ("rssHeadroomBytes" (hash-ref observation "rssHeadroomBytes"))
   ("maxRssBytes" (hash-ref observation "maxRssBytes"))
   ("processTreeRssAvailable" (hash-ref observation "processTreeRssAvailable"))
   ("peakRssBytes" peak-rss-bytes)
   ("elapsedMs" elapsed-ms)
   ("timeoutMs" (and timeout-seconds (* timeout-seconds 1000)))
   ("admissionOutcome" (hash-ref observation "admissionOutcome"))
   ("admissionAdvisories" (hash-ref observation "admissionAdvisories"))
   ("admissionReasons" (hash-ref observation "admissionReasons"))))

(def (receipt-json receipt)
  (parameterize ((write-json-sort-keys? #t))
    (json-object->string receipt)))

(def (write-receipt! path receipt)
  (let (payload (receipt-json receipt))
    (call-with-output-file path
      (lambda (port)
        (display payload port)
        (newline port)))
    (display "GERBIL_BAZEL_RESOURCE_GUARD_RECEIPT " (current-error-port))
    (display payload (current-error-port))
    (newline (current-error-port))
    (force-output (current-error-port))))

(def (run-guarded label observation timeout-seconds sample-seconds argv)
  (let* ((started (now-seconds))
         (child
          (open-process
           (list path: (car argv)
                 arguments: (cdr argv)
                 stdin-redirection: #f
                 stdout-redirection: #f
                 stderr-redirection: #f)))
         (pid (process-pid child))
         (state (vector #f #f))
         (waiter
          (spawn
           (lambda ()
             (vector-set! state 1 (normalized-exit-code (process-status child)))
             (vector-set! state 0 #t))))
         (peak-rss 0)
         (outcome 'running)
         (guard-exit 0))
    (let loop ()
      (unless (vector-ref state 0)
        (let* ((rss (process-tree-rss-bytes pid))
               (elapsed (- (now-seconds) started)))
          (set! peak-rss (max peak-rss rss))
          (cond
           ((> peak-rss (hash-ref observation "maxRssBytes"))
            (set! outcome 'rss-limit-exceeded)
            (set! guard-exit 70)
            (terminate-process-tree! pid))
           ((and timeout-seconds (> elapsed timeout-seconds))
            (set! outcome 'timeout)
            (set! guard-exit 71)
            (terminate-process-tree! pid))
           (else
            (thread-sleep! sample-seconds)
            (loop))))))
    (thread-join! waiter)
    (close-port child)
    (let* ((child-exit (vector-ref state 1))
           (final-outcome (if (eq? outcome 'running) 'completed outcome))
           (final-exit (if (eq? outcome 'running) child-exit guard-exit))
           (elapsed-ms
            (inexact->exact (round (* 1000 (- (now-seconds) started))))))
      (guard-receipt label observation final-outcome final-exit child-exit
                     peak-rss elapsed-ms timeout-seconds))))

(def (main receipt-path label declared-timeout-text . argv)
  (unless (pair? argv)
    (error "usage: resource_guard.ss RECEIPT LABEL TIMEOUT_SECONDS COMMAND [ARG ...]"
           argv))
  (let (declared-timeout (string->number declared-timeout-text))
    (unless (and (exact-integer? declared-timeout) (>= declared-timeout 0))
      (error "declared guard timeout must be a non-negative integer"
             declared-timeout-text))
    (let* ((observation (host-observation))
           (timeout-seconds (optional-timeout declared-timeout))
           (sample-seconds
            (positive-real-from-env
             "GERBIL_BAZEL_GUARD_SAMPLE_SECONDS"
             +default-sample-seconds+))
           (blocked?
            (not (string=? (hash-ref observation "admissionOutcome") "ready")))
           (receipt
            (if blocked?
                (guard-receipt label observation 'blocked-host-pressure 72 #f 0 0
                               timeout-seconds)
                (run-guarded label observation timeout-seconds sample-seconds argv))))
      (write-receipt! receipt-path receipt)
      (exit (hash-ref receipt "exitCode")))))
