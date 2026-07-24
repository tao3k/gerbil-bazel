(export package-value-test)

(import :std/test
        :example.invalid/test-package/src/value)

(def package-value-test
  (test-suite "public package consumer"
    (test-case "loads the built package through GerbilPackageInfo"
      (check-eq? (package-value) 'public-package-consumer))))
