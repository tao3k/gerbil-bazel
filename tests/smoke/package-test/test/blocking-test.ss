(export blocking-test)

(import :std/test)

(def blocking-test
  (test-suite "terminal process lifecycle"
    (test-case "remains alive until the lifecycle harness signals it"
      (let loop ()
        (thread-yield!)
        (loop)))))
