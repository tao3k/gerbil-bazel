(import :gerbil/tools/gxtest :std/test/base :std/encoding/json)

(def wanted (getenv "MCP_ATOMIC_CASE"))
(def prepare (##eval 'gerbil/tools/gxtest#prepare-harness))
(def harness (prepare (list (getenv "MCP_ATOMIC_FILE")) (lambda (_) #t) 5))
(def selected 0)
(using (harness :- TestHarness)
 (for-each
 (lambda ((mod : TestModule))
   (for-each
    (lambda ((suite : TestSuite))
      (let (initialize suite.init!)
        (set! suite.init!
          (lambda ()
            (initialize)
            (set! suite.subtests
              (filter (lambda ((tc : TestCase)) (equal? tc.info wanted)) suite.subtests))
            (for-each
             (lambda ((tc : TestCase))
               (set! selected (+ selected 1))
               (let (body tc.main)
                 (set! tc.main
                   (lambda ()
                     (let (started (real-time))
                       (try (body)
                         (finally
                          (displayln (json->string
                                       (hash ("atomicCase" wanted)
                                             ("caseWallSeconds" (- (real-time) started)))))
                          (force-output))))))))
             suite.subtests)))))
    mod.subtests))
 harness.subtests))
(def result (test-run! harness))
(if (and (= selected 1) (test-result-ok? result))
  (begin (displayln "OK") (force-output) (exit 0))
  (begin (displayln "ATOMIC-FAIL") (force-output) (exit 42)))
