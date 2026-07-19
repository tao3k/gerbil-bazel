#!/usr/bin/env gxi

(import :std/build-script)

(defbuild-script
  '("native-math/lib"
    (exe: "native-math/main" bin: "native-math")))
