(export main)

(import :example.invalid/native-math/lib)

(def (main)
  (unless (zero? (native-math-log 1))
    (error "native math executable returned an unexpected logarithm"))
  (displayln "gxpkg-native-package-ok"))
