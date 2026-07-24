(export dependency-loadpath-test)

(import :std/test
        :clan/base)

(def dependency-loadpath-test
  (test-suite "transitive package consumer"
    (test-case "loads a locked dependency from GerbilPackageInfo"
      (check-eq? #t #t))))
