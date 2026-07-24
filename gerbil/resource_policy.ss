(import :gerbil/gambit
        :std/sugar
        :std/misc/path
        :std/misc/ports
        :std/misc/process
        :std/srfi/13
        :std/text/json)

(def +resource-guard-schema+
  "gerbil-bazel.resource-guard-receipt.v1")
(def +resource-budget-schema+
  "gerbil-bazel.resource-budget.v1")
(def +minimum-max-rss-bytes+ (* 768 1024 1024))
(def +default-memory-per-core-bytes+ (* 2 1024 1024 1024))
(def +headroom-share-denominator+ 16)
(def +runnable-limit-per-cpu+ 2)
(def +default-sample-seconds+ 0.25)
(def +maximum-cgroup-memory-bytes+ 1152921504606846976)

(def (now-seconds)
  (time->seconds (current-time)))

(include "functional.ss")

(def (positive-integer-from-env name fallback)
  (or (positive-integer (getenv name #f)) fallback))

(def (non-negative-integer-from-env name fallback)
  (let (value (getenv name #f))
    (if value (non-negative-integer value) fallback)))

(def (positive-real-from-env name fallback)
  (let* ((raw (getenv name #f))
         (value (and raw (string->number raw))))
    (if (and (real? value) (> value 0)) value fallback)))

(def (required-positive-integer-from-env name fallback)
  (let (raw (getenv name #f))
    (cond
     ((not raw) fallback)
     ((positive-integer raw))
     (else
      (error (string-append name " must be a positive integer") raw)))))

(def (optional-timeout declared-timeout)
  (let* ((raw (getenv "GERBIL_BAZEL_GUARD_TIMEOUT_SECONDS" #f))
         (value (and raw (string->number raw))))
    (cond
     ((and raw (exact-integer? value) (= value 0)) #f)
     ((and raw (exact-integer? value) (> value 0)) value)
     (raw
      (error
       "GERBIL_BAZEL_GUARD_TIMEOUT_SECONDS must be a non-negative integer"
       raw))
     ((> declared-timeout 0) declared-timeout)
     (else #f))))

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

(def (system-tool name)
  (let loop
      ((directories '("/usr/bin" "/bin" "/usr/sbin" "/sbin")))
    (if (null? directories)
        name
        (let (candidate
              (path-expand name (car directories)))
          (if (file-exists? candidate)
              candidate
              (loop (cdr directories)))))))

(def (command-positive-integer argv)
  (let* ((result (run-captured argv))
         (value
          (and (= (car result) 0)
               (positive-integer (string-trim-both (cdr result))))))
    value))

(def (read-first-line path)
  (with-catch
   (lambda (_error) #f)
   (lambda ()
     (let (lines (read-file-lines path))
       (and (pair? lines) (car lines))))))

(def (read-positive-integer-file path)
  (let (line (read-first-line path))
    (and line (positive-integer (string-trim-both line)))))

(def (read-non-negative-integer-file path)
  (let (line (read-first-line path))
    (and
     line
     (non-negative-integer
      (string-trim-both line)))))

(def (logical-cpu-count)
  (required-positive-integer-from-env
   "GERBIL_BAZEL_GUARD_LOGICAL_CPU_COUNT"
   (max 1 (##cpu-count))))

(def (runnable-process-count)
  (or
   (positive-integer-from-env
    "GERBIL_BAZEL_GUARD_RUNNABLE_PROCESSES"
    #f)
   (let (result
         (run-captured
          (list (system-tool "ps") "-axo" "state=")))
     (and
      (= (car result) 0)
      (let loop ((lines (string-split (cdr result) #\newline))
                 (count 0))
        (if (null? lines)
            (max 1 count)
            (let (line (string-trim-both (car lines)))
              (loop
               (cdr lines)
               (if (and (> (string-length line) 0)
                        (char=? (string-ref line 0) #\R))
                   (+ count 1)
                   count)))))))
   1))

(def (linux-cgroup-memory-state)
  (or
   (let ((limit
          (positive-integer-from-env
           "GERBIL_BAZEL_GUARD_CGROUP_MEMORY_LIMIT_BYTES"
           #f))
         (current
          (non-negative-integer-from-env
           "GERBIL_BAZEL_GUARD_CGROUP_MEMORY_CURRENT_BYTES"
           #f)))
     (and
      limit
      (< limit +maximum-cgroup-memory-bytes+)
      (cons limit current)))
   (let loop
       ((path-pairs
         '(("/sys/fs/cgroup/memory.max"
            "/sys/fs/cgroup/memory.current")
           ("/sys/fs/cgroup/memory/memory.limit_in_bytes"
            "/sys/fs/cgroup/memory/memory.usage_in_bytes"))))
     (and
      (pair? path-pairs)
      (let* ((paths (car path-pairs))
             (limit
              (read-positive-integer-file (car paths)))
             (current
              (read-non-negative-integer-file
               (cadr paths))))
        (if
         (and
          limit
          (< limit +maximum-cgroup-memory-bytes+))
         (cons limit current)
         (loop (cdr path-pairs))))))))

(def (linux-cgroup-memory-limit-bytes)
  (let (state (linux-cgroup-memory-state))
    (and state (car state))))

(def (linux-cgroup-available-memory-bytes)
  (let (state (linux-cgroup-memory-state))
    (and
     state
     (cdr state)
     (max 0 (- (car state) (cdr state))))))

(def (system-memory-bytes)
  (or
   (positive-integer-from-env
    "GERBIL_BAZEL_GUARD_SYSTEM_MEMORY_BYTES"
    #f)
   (positive-integer-from-env
    "GERBIL_BAZEL_MEMORY_BYTES"
    #f)
   (linux-cgroup-memory-limit-bytes)
   (command-positive-integer
    (list (system-tool "sysctl") "-n" "hw.memsize"))
   (let ((pages
          (command-positive-integer
           (list (system-tool "getconf") "_PHYS_PAGES")))
         (page-size
          (command-positive-integer
           (list (system-tool "getconf") "PAGE_SIZE"))))
     (and pages page-size (* pages page-size)))
   (* 8 +minimum-max-rss-bytes+)))

(def (linux-available-memory-bytes)
  (with-catch
   (lambda (_error) #f)
   (lambda ()
     (let loop ((lines (read-file-lines "/proc/meminfo")))
       (and
        (pair? lines)
        (let* ((tokens (string-tokenize (car lines)))
               (value
                (and
                 (>= (length tokens) 2)
                 (string=? (car tokens) "MemAvailable:")
                 (positive-integer (cadr tokens)))))
          (if value (* value 1024) (loop (cdr lines)))))))))

(def (darwin-available-memory-percent)
  (let (result
        (run-captured
         (list (system-tool "memory_pressure") "-Q")))
    (and
     (= (car result) 0)
     (let loop ((lines (string-split (cdr result) #\newline)))
       (and
        (pair? lines)
        (let* ((tokens (string-tokenize (car lines)))
               (last-token (and (pair? tokens) (last tokens)))
               (length (and last-token (string-length last-token)))
               (value
                (and
                 last-token
                 (> length 1)
                 (char=? (string-ref last-token (- length 1)) #\%)
                 (positive-integer
                  (substring last-token 0 (- length 1))))))
          (if value value (loop (cdr lines)))))))))

(def (available-memory-bytes total-memory)
  (let* ((explicit
          (positive-integer-from-env
           "GERBIL_BAZEL_GUARD_AVAILABLE_MEMORY_BYTES"
           #f))
         (observation-enabled
          (not
           (getenv
            "GERBIL_BAZEL_GUARD_FORCE_AVAILABLE_MEMORY_UNAVAILABLE"
            #f)))
         (os-available
          (and
           observation-enabled
           (or
            (linux-available-memory-bytes)
            (let (percent (darwin-available-memory-percent))
              (and
               percent
               (quotient
                (* total-memory percent)
                100))))))
         (cgroup-available
          (and
           observation-enabled
           (linux-cgroup-available-memory-bytes)))
         (observed
          (cond
           ((and os-available cgroup-available)
            (min os-available cgroup-available))
           (cgroup-available cgroup-available)
           (os-available os-available)
           (else 0))))
    (min total-memory (or explicit observed))))

(def (default-headroom-bytes total-memory)
  (max
   +minimum-max-rss-bytes+
   (quotient total-memory +headroom-share-denominator+)))

(def (live-process-table-result)
  (run-captured
   (list (system-tool "ps") "-axo" "pid=,ppid=,rss=")))

(def (process-table-result)
  (cond
   ((getenv "GERBIL_BAZEL_GUARD_FORCE_PROCESS_TABLE_UNAVAILABLE" #f)
    (cons 126 ""))
   ((getenv "GERBIL_BAZEL_GUARD_PROCESS_TABLE_SNAPSHOT" #f)
    => (lambda (snapshot) (cons 0 snapshot)))
   (else
    (live-process-table-result))))

(def (process-row line)
  (let (tokens (string-tokenize line))
    (and
     (= (length tokens) 3)
     (let ((pid (string->number (car tokens)))
           (ppid (string->number (cadr tokens)))
           (rss-kib (string->number (caddr tokens))))
       (and pid ppid rss-kib (list pid ppid (* rss-kib 1024)))))))

(def (process-table-from-result result)
  (if (= (car result) 0)
      (filter-map
       process-row
       (string-split (cdr result) #\newline))
      '()))

(def (process-table)
  (process-table-from-result (process-table-result)))

(def (live-process-table)
  (process-table-from-result (live-process-table-result)))

(def (host-observation)
  (let* ((total-memory (system-memory-bytes))
         (available-memory (available-memory-bytes total-memory))
         (headroom
          (positive-integer-from-env
           "GERBIL_BAZEL_GUARD_RSS_HEADROOM_BYTES"
           (default-headroom-bytes total-memory)))
         (available-max-rss (max 1 (- available-memory headroom)))
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
           (cond
            ((= available-memory 0)
             '(available-memory-unavailable))
            ((< available-memory
                (+ headroom +minimum-max-rss-bytes+))
             '(insufficient-memory-headroom))
            (else '()))
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
     ("admissionOutcome"
      (if (null? reasons) "ready" "blocked-host-pressure"))
     ("admissionAdvisories" (map symbol->string advisories))
     ("admissionReasons" (map symbol->string reasons)))))

(def (resolve-build-budget
      observation
      explicit-cores-env:
      (explicit-cores-env #f)
      memory-per-core-env:
      (memory-per-core-env "GERBIL_BAZEL_MEMORY_PER_CORE_BYTES"))
  (let* ((logical-cpus (hash-ref observation "logicalCpuCount"))
         (configured-cores
          (required-positive-integer-from-env
           "GERBIL_BUILD_CORES"
           logical-cpus))
         (explicit-cores
          (and
           explicit-cores-env
           (required-positive-integer-from-env
            explicit-cores-env
            #f)))
         (memory-per-core
          (required-positive-integer-from-env
           memory-per-core-env
           +default-memory-per-core-bytes+))
         (memory-core-limit
          (max
           1
           (quotient
            (hash-ref observation "maxRssBytes")
            memory-per-core)))
         (requested-cores
          (or explicit-cores configured-cores logical-cpus))
         (selected-cores
          (max 1 (min requested-cores logical-cpus memory-core-limit)))
         (decision
          (cond
           ((and explicit-cores (< selected-cores explicit-cores))
            "explicit-memory-cap")
           (explicit-cores "explicit")
           ((< selected-cores configured-cores) "adaptive-memory-cap")
           (else "adaptive-configured"))))
    (hash
     ("schema" +resource-budget-schema+)
     ("decision" decision)
     ("selectedCores" selected-cores)
     ("requestedCores" requested-cores)
     ("configuredCores" configured-cores)
     ("logicalCpuCount" logical-cpus)
     ("memoryPerCoreBytes" memory-per-core)
     ("memoryCoreLimit" memory-core-limit)
     ("availableMemoryBytes"
      (hash-ref observation "availableMemoryBytes"))
     ("maxRssBytes" (hash-ref observation "maxRssBytes")))))

(def (apply-build-budget! budget)
  (setenv
   "GERBIL_BUILD_CORES"
   (number->string (hash-ref budget "selectedCores"))))

(def (process-tree-pids root-pid rows)
  (let expand ((known (list root-pid)))
    (let lp ((rest rows) (next known) (changed? #f))
      (if (null? rest)
          (if changed? (expand next) next)
          (let* ((row (car rest))
                 (pid (car row))
                 (ppid (cadr row)))
            (if (and
                 (member ppid next)
                 (not (member pid next)))
                (lp (cdr rest) (cons pid next) #t)
                (lp (cdr rest) next changed?)))))))

(def (process-tree-rss-bytes pid)
  (let* ((rows (process-table))
         (tree-pids (process-tree-pids pid rows)))
    (foldl
     (lambda (row total)
       (if (member (car row) tree-pids)
           (+ total (caddr row))
           total))
     0
     rows)))

(def (signal-process! signal pid)
  (= (car
      (run-captured
       (list
        (system-tool "kill")
        signal
        (number->string pid))))
     0))

(def (new-process-tree-pids observed known)
  (filter-map
   (lambda (observed-pid)
     (and (not (member observed-pid known)) observed-pid))
   observed))

(def (freeze-process-tree-pids! pid)
  (signal-process! "-STOP" pid)
  (let loop ((known (list pid)))
    (let* ((tree-pids
            (process-tree-pids pid (live-process-table)))
           (new-pids
            (new-process-tree-pids tree-pids known)))
      (for-each
       (lambda (new-pid)
         (signal-process! "-STOP" new-pid))
       new-pids)
      (if (null? new-pids)
          tree-pids
          (loop tree-pids)))))

(def (terminate-process-tree! pid)
  (let (tree-pids (freeze-process-tree-pids! pid))
    (for-each
     (lambda (tree-pid)
       (signal-process! "-KILL" tree-pid))
     tree-pids)))

(def (guard-receipt
      label
      observation
      outcome
      exit-code
      child-exit-code
      peak-rss-bytes
      elapsed-ms
      timeout-seconds)
  (hash
   ("kind" +resource-guard-schema+)
   ("schema" +resource-guard-schema+)
   ("version" 1)
   ("label" label)
   ("outcome" (symbol->string outcome))
   ("exitCode" exit-code)
   ("childExitCode" child-exit-code)
   ("logicalCpuCount" (hash-ref observation "logicalCpuCount"))
   ("runnableProcessCount"
    (hash-ref observation "runnableProcessCount"))
   ("systemMemoryBytes" (hash-ref observation "systemMemoryBytes"))
   ("availableMemoryBytes"
    (hash-ref observation "availableMemoryBytes"))
   ("rssHeadroomBytes" (hash-ref observation "rssHeadroomBytes"))
   ("maxRssBytes" (hash-ref observation "maxRssBytes"))
   ("processTreeRssAvailable"
    (hash-ref observation "processTreeRssAvailable"))
   ("peakRssBytes" peak-rss-bytes)
   ("elapsedMs" elapsed-ms)
   ("timeoutMs"
    (and timeout-seconds (* timeout-seconds 1000)))
   ("admissionOutcome"
    (hash-ref observation "admissionOutcome"))
   ("admissionAdvisories"
    (hash-ref observation "admissionAdvisories"))
   ("admissionReasons"
    (hash-ref observation "admissionReasons"))))

(def (blocked-guard-receipt observation label timeout-seconds)
  (guard-receipt
   label
   observation
   'blocked-host-pressure
   72
   #f
   0
   0
   timeout-seconds))

(def (receipt-json receipt)
  (parameterize ((write-json-sort-keys? #t))
    (json-object->string receipt)))

(def (write-json-file! path value)
  (write-file-string path (receipt-json value)))

(def (write-guard-receipt! path receipt)
  (write-json-file! path receipt)
  (display
   "GERBIL_BAZEL_RESOURCE_GUARD_RECEIPT "
   (current-error-port))
  (display (receipt-json receipt) (current-error-port))
  (newline (current-error-port))
  (force-output (current-error-port)))

(def (run-guarded
      label
      observation
      timeout-seconds
      sample-seconds
      argv
      directory:
      (directory #f)
      output-path:
      (output-path #f))
  (let* ((started (now-seconds))
         (child
          (open-process
           (list
            path: (car argv)
            arguments: (cdr argv)
            directory: directory
            stdin-redirection: #f
            stdout-redirection: (if output-path #t #f)
            stderr-redirection: (if output-path #t #f))))
         (pid (process-pid child))
         (state (vector #f #f))
         (drainer
          (and
           output-path
           (spawn
            (lambda ()
              (call-with-output-file
               output-path
               (lambda (output)
                 (copy-port child output)))))))
         (waiter
          (spawn
           (lambda ()
             (vector-set!
              state
              1
              (normalized-exit-code (process-status child)))
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
    (when drainer
      (thread-join! drainer))
    (close-port child)
    (let* ((child-exit (vector-ref state 1))
           (final-outcome
            (if (eq? outcome 'running) 'completed outcome))
           (final-exit
            (if (eq? outcome 'running) child-exit guard-exit))
           (elapsed-ms
            (inexact->exact
             (round (* 1000 (- (now-seconds) started))))))
      (guard-receipt
       label
       observation
       final-outcome
       final-exit
       child-exit
       peak-rss
       elapsed-ms
       timeout-seconds))))

(def (guard-command
      label
      declared-timeout
      argv
      directory:
      (directory #f)
      output-path:
      (output-path #f))
  (let* ((observation (host-observation))
         (timeout-seconds (optional-timeout declared-timeout))
         (sample-seconds
          (positive-real-from-env
           "GERBIL_BAZEL_GUARD_SAMPLE_SECONDS"
           +default-sample-seconds+))
         (blocked?
          (not
           (string=?
            (hash-ref observation "admissionOutcome")
            "ready"))))
    (if blocked?
        (blocked-guard-receipt
         observation
         label
         timeout-seconds)
        (run-guarded
         label
         observation
         timeout-seconds
         sample-seconds
         argv
         directory: directory
         output-path: output-path))))
