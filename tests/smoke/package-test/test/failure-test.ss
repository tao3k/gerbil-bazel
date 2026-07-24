(export expected-failure-test)

(import :std/test)

(def expected-failure-test
  (test-suite "deterministic failure propagation"
    (test-case "returns the gxtest failure status"
      (check-eq? 'actual 'expected))))
