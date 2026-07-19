#!/usr/bin/env gxi

(import :compile-target)

(unless (eq? (gerbil-bazel-smoke-value) 'ready)
  (error "gerbil-bazel compiled module is not ready"))

(displayln "gerbil-bazel smoke test")
