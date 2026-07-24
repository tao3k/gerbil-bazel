(include "resource_policy.ss")

(def (main receipt-path label declared-timeout-text . argv)
  (unless (pair? argv)
    (error
     "usage: resource_guard.ss RECEIPT LABEL TIMEOUT_SECONDS COMMAND [ARG ...]"
     argv))
  (let (declared-timeout (string->number declared-timeout-text))
    (unless
     (and
      (exact-integer? declared-timeout)
      (>= declared-timeout 0))
      (error
       "declared guard timeout must be a non-negative integer"
       declared-timeout-text))
    (let (receipt
          (guard-command label declared-timeout argv))
      (write-guard-receipt! receipt-path receipt)
      (exit (hash-ref receipt "exitCode")))))
