#!/usr/bin/env gxi
;;; -*- Gerbil -*-
;;; Scheme-owned host admission, process-tree RSS, and deadline guard.

(export main)

(import :gerbil/gambit
        (only-in :gerbil/compiler/base __available-cores)
        (only-in :std/misc/process run-process)
        (only-in :std/srfi/13
                 string-prefix?
                 string-trim-both
                 string-tokenize)
        (only-in :std/text/json json-object->string write-json-sort-keys?))

(def +resource-guard-schema+ "gerbil-bazel.resource-guard-receipt.v1")
(def +resource-guard-admission-schema+
  "gerbil-bazel.resource-guard-admission.v1")
(def +minimum-max-rss-bytes+ (* 768 1024 1024))
(def +maximum-default-memory-per-core-bytes+ (* 2 1024 1024 1024))
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

(def (required-positive-integer-from-env name fallback)
  (let* ((raw (getenv name #f))
         (value (and raw (string->number raw))))
    (cond
     ((not raw) fallback)
     ((and (exact-integer? value) (> value 0)) value)
     (else (error (string-append name " must be a positive integer") raw)))))

(def (optional-timeout declared-timeout)
  (let* ((raw (getenv "GERBIL_BAZEL_GUARD_TIMEOUT_SECONDS" #f))
         (value (and raw (string->number raw))))
    (cond
     ((and raw (exact-integer? value) (= value 0)) #f)
     ((and raw (exact-integer? value) (> value 0)) value)
     (raw (error "GERBIL_BAZEL_GUARD_TIMEOUT_SECONDS must be a non-negative integer" raw))
     ((> declared-timeout 0) declared-timeout)
     (else #f))))

(def (available-core-count)
  ;; Gerbil owns the build-capacity contract.  `__available-cores` is already
  ;; initialized from GERBIL_BUILD_CORES by the compiler runtime, so probing
  ;; ##cpu-count or the host again would create a second source of truth.
  (max 1 __available-cores))

(def (runnable-state-line? line)
  (string-prefix? "R" (string-trim-both line)))

(def (runnable-process-count-from-state-output output)
  (let loop ((states (string-split output #\newline))
             (count 0))
    (if (null? states)
      count
      (loop
       (cdr states)
       (if (runnable-state-line? (car states))
         (+ count 1)
         count)))))

(def (live-runnable-state-result)
  (run-captured (list "ps" "-axo" "state=")))

(def (runnable-state-result)
  (cond
   ((getenv "GERBIL_BAZEL_GUARD_RUNNABLE_STATE_SNAPSHOT" #f)
    => (lambda (snapshot) (cons 0 snapshot)))
   (else
    (live-runnable-state-result))))

(def (runnable-process-observation)
  ;; CPU capacity comes from Gerbil.  Runnable pressure is a fresh observation:
  ;; invoke ps directly and parse its state column in Scheme, never through a
  ;; shell pipeline.  Apart from deterministic failure injection, an explicit
  ;; count remains the highest-priority CI observation.
  (if (getenv "GERBIL_BAZEL_GUARD_FORCE_RUNNABLE_UNAVAILABLE" #f)
    (cons #f 0)
    (let* ((explicit-raw
            (getenv "GERBIL_BAZEL_GUARD_RUNNABLE_PROCESSES" #f))
           (explicit-count
            (and explicit-raw (string->number explicit-raw))))
      (if (and (exact-integer? explicit-count) (>= explicit-count 0))
        (cons #t explicit-count)
        (let (result (runnable-state-result))
          (if (= (car result) 0)
            (cons
             #t
             (runnable-process-count-from-state-output (cdr result)))
            (cons #f 0)))))))

(def (system-memory-bytes)
  (or (positive-integer-from-env
       "GERBIL_BAZEL_GUARD_SYSTEM_MEMORY_BYTES"
       #f)
      (positive-integer-from-env
       "GERBIL_BAZEL_MEMORY_BYTES"
       #f)
      (command-positive-integer (list "sysctl" "-n" "hw.memsize"))
      (let ((pages (command-positive-integer (list "getconf" "_PHYS_PAGES")))
            (page-size (command-positive-integer (list "getconf" "PAGE_SIZE"))))
        (and pages page-size (* pages page-size)))
      (* 8 +minimum-max-rss-bytes+)))

(def (linux-available-memory-bytes)
  (with-catch
   (lambda (_error) #f)
   (lambda ()
     (and
      (file-exists? "/proc/meminfo")
      (call-with-input-file
       "/proc/meminfo"
       (lambda (port)
         (let loop ()
           (let (line (read-line port))
             (cond
              ((eof-object? line) #f)
              ((string-prefix? "MemAvailable:" line)
               (let* ((tokens (string-tokenize line))
                      (kilobytes
                       (and (pair? tokens)
                            (pair? (cdr tokens))
                            (string->number (cadr tokens)))))
                 (and (exact-integer? kilobytes)
                      (> kilobytes 0)
                      (* kilobytes 1024))))
              (else (loop)))))))))))

(def (last-token tokens)
  (and
   (pair? tokens)
   (let loop ((rest tokens))
     (if (pair? (cdr rest))
       (loop (cdr rest))
       (car rest)))))

(def (find-output-line output prefix)
  (let (port (open-input-string output))
    (unwind-protect
      (let loop ()
        (let (line (read-line port))
          (cond
           ((eof-object? line) #f)
           ((string-prefix? prefix line) line)
           (else (loop)))))
      (close-input-port port))))

(def (darwin-available-memory-percent)
  (let* ((result (run-captured (list "memory_pressure" "-Q")))
         (line
          (and
           (= (car result) 0)
           (find-output-line
            (cdr result)
            "System-wide memory free percentage:")))
         (percent-token
          (and line (last-token (string-tokenize line))))
         (percent
          (and
           percent-token
           (> (string-length percent-token) 1)
           (string->number
            (substring
             percent-token
             0
             (- (string-length percent-token) 1))))))
    (and (exact-integer? percent)
         (> percent 0)
         (<= percent 100)
         percent)))

(def (available-memory-bytes total-memory)
  (or (positive-integer-from-env
       "GERBIL_BAZEL_GUARD_AVAILABLE_MEMORY_BYTES"
       #f)
      (and
       (not
        (getenv
         "GERBIL_BAZEL_GUARD_FORCE_AVAILABLE_MEMORY_UNAVAILABLE"
         #f))
       (or
        (linux-available-memory-bytes)
        (let (percent (darwin-available-memory-percent))
          (and percent (quotient (* total-memory percent) 100)))))
      0))

(def (default-headroom-bytes total-memory)
  (max +minimum-max-rss-bytes+
       (quotient total-memory +headroom-share-denominator+)))

(def (adaptive-memory-per-core-bytes observation logical-cpus)
  (max
   +minimum-max-rss-bytes+
   (min
    +maximum-default-memory-per-core-bytes+
    (quotient (hash-ref observation "maxRssBytes") logical-cpus))))

(def (runnable-build-core-limit observation)
  (let* ((logical-cpus (hash-ref observation "logicalCpuCount"))
         (runnable (hash-ref observation "runnableProcessCount"))
         ;; The runnable-process probe normally observes itself. Preserve that
         ;; one slot, then fill only CPU capacity not already claimed by other
         ;; runnable processes.
         (other-runnable (max 0 (- runnable 1))))
    (if (< other-runnable logical-cpus)
      (max 1 (- logical-cpus other-runnable))
      (max 1
           (quotient (* logical-cpus logical-cpus)
                     other-runnable)))))

(def (build-core-plan observation)
  (let* ((logical-cpus (hash-ref observation "logicalCpuCount"))
         (requested-cores
          (required-positive-integer-from-env
           "GERBIL_BUILD_CORES"
           (max 1 __available-cores)))
         (memory-per-core
          (required-positive-integer-from-env
           "GERBIL_BAZEL_MEMORY_PER_CORE_BYTES"
           (adaptive-memory-per-core-bytes observation logical-cpus)))
         (memory-core-limit
          (max
           1
           (quotient
            (hash-ref observation "maxRssBytes")
            memory-per-core)))
         (runnable-core-limit (runnable-build-core-limit observation))
         (effective-cores
          (max
           1
           (min requested-cores
                logical-cpus
                memory-core-limit))))
    (hash
     ("requestedBuildCoreCount" requested-cores)
     ("effectiveBuildCoreCount" effective-cores)
     ("memoryCoreLimit" memory-core-limit)
     ("memoryPerCoreBytes" memory-per-core)
     ;; Keep the v1 diagnostic projection stable, but do not use a transient
     ;; host-wide runnable sample as Gerbil build capacity.  Upstream std/make
     ;; models safe parallelism from CPU count and memory per compilation core.
     ("runnableCoreLimit" runnable-core-limit)
     ("runnableCoreLimitApplied" #f))))

(def (apply-build-core-plan! plan)
  (setenv
   "GERBIL_BUILD_CORES"
   (number->string (hash-ref plan "effectiveBuildCoreCount"))))

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
         (logical-cpus (available-core-count))
         (runnable-observation (runnable-process-observation))
         (runnable (cdr runnable-observation))
         (runnable-available? (car runnable-observation))
         (process-table-probe (process-table-result))
         (process-tree-rss-available? (= (car process-table-probe) 0))
         (advisories
          (if (and runnable-available?
                   (> runnable (* logical-cpus +runnable-limit-per-cpu+)))
              '(runnable-saturation)
              '()))
         (reasons
          (append
           (cond
            ((= available-memory 0)
             '(available-memory-unavailable))
            ((< available-memory (+ headroom +minimum-max-rss-bytes+))
             '(insufficient-memory-headroom))
            (else
             '()))
           (if process-tree-rss-available?
               '()
               '(process-tree-rss-unavailable)))))
    (hash
     ("logicalCpuCount" logical-cpus)
     ("runnableProcessCount" runnable)
     ("runnableProcessCountAvailable" runnable-available?)
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

(def (guard-receipt label observation plan outcome exit-code child-exit-code
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
   ("runnableProcessCountAvailable"
    (hash-ref observation "runnableProcessCountAvailable"))
   ("requestedBuildCoreCount" (hash-ref plan "requestedBuildCoreCount"))
   ("effectiveBuildCoreCount" (hash-ref plan "effectiveBuildCoreCount"))
   ("memoryCoreLimit" (hash-ref plan "memoryCoreLimit"))
   ("memoryPerCoreBytes" (hash-ref plan "memoryPerCoreBytes"))
   ("runnableCoreLimit" (hash-ref plan "runnableCoreLimit"))
   ("runnableCoreLimitApplied" (hash-ref plan "runnableCoreLimitApplied"))
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

(def (admission-receipt label observation plan timeout-seconds)
  (hash
   ("kind" +resource-guard-admission-schema+)
   ("schema" +resource-guard-admission-schema+)
   ("version" 1)
   ("label" label)
   ("admissionOutcome" (hash-ref observation "admissionOutcome"))
   ("admissionAdvisories" (hash-ref observation "admissionAdvisories"))
   ("admissionReasons" (hash-ref observation "admissionReasons"))
   ("logicalCpuCount" (hash-ref observation "logicalCpuCount"))
   ("runnableProcessCount" (hash-ref observation "runnableProcessCount"))
   ("runnableProcessCountAvailable"
    (hash-ref observation "runnableProcessCountAvailable"))
   ("requestedBuildCoreCount" (hash-ref plan "requestedBuildCoreCount"))
   ("effectiveBuildCoreCount" (hash-ref plan "effectiveBuildCoreCount"))
   ("memoryCoreLimit" (hash-ref plan "memoryCoreLimit"))
   ("memoryPerCoreBytes" (hash-ref plan "memoryPerCoreBytes"))
   ("runnableCoreLimit" (hash-ref plan "runnableCoreLimit"))
   ("runnableCoreLimitApplied" (hash-ref plan "runnableCoreLimitApplied"))
   ("systemMemoryBytes" (hash-ref observation "systemMemoryBytes"))
   ("availableMemoryBytes" (hash-ref observation "availableMemoryBytes"))
   ("rssHeadroomBytes" (hash-ref observation "rssHeadroomBytes"))
   ("maxRssBytes" (hash-ref observation "maxRssBytes"))
   ("processTreeRssAvailable" (hash-ref observation "processTreeRssAvailable"))
   ("timeoutMs" (and timeout-seconds (* timeout-seconds 1000)))))

(def (receipt-json receipt)
  (parameterize ((write-json-sort-keys? #t))
    (json-object->string receipt)))

(def (emit-receipt! prefix receipt)
  (let (payload (receipt-json receipt))
    (display prefix (current-error-port))
    (display payload (current-error-port))
    (newline (current-error-port))
    (force-output (current-error-port))))

(def (write-receipt! path receipt)
  (let (payload (receipt-json receipt))
    (call-with-output-file path
      (lambda (port)
        (display payload port)
        (newline port))))
  (emit-receipt! "GERBIL_BAZEL_RESOURCE_GUARD_RECEIPT " receipt))

(def (run-guarded label observation plan timeout-seconds sample-seconds argv)
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
      (guard-receipt label observation plan final-outcome final-exit child-exit
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
           (plan (build-core-plan observation))
           (timeout-seconds (optional-timeout declared-timeout))
           (sample-seconds
            (positive-real-from-env
             "GERBIL_BAZEL_GUARD_SAMPLE_SECONDS"
             +default-sample-seconds+))
           (blocked?
            (not (string=? (hash-ref observation "admissionOutcome") "ready")))
           (_admission
            (emit-receipt!
             "GERBIL_BAZEL_RESOURCE_GUARD_ADMISSION "
             (admission-receipt label observation plan timeout-seconds)))
           (receipt
            (if blocked?
                (guard-receipt label observation plan 'blocked-host-pressure
                               72 #f 0 0 timeout-seconds)
                (begin
                  (apply-build-core-plan! plan)
                  (run-guarded
                   label
                   observation
                   plan
                   timeout-seconds
                   sample-seconds
                   argv)))))
      (write-receipt! receipt-path receipt)
      (exit (hash-ref receipt "exitCode")))))
