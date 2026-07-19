#!/usr/bin/env gxi

(import :source-root-support)

(unless (eq? source-root-ready 'ready)
  (error "source-root support module did not resolve"))

(displayln "gerbil-bazel source-root test")
