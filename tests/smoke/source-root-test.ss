#!/usr/bin/env gxi

(import :std/text/json
        :source-root-support)

(unless (eq? source-root-ready 'ready)
  (error "source-root support module did not resolve"))

(unless
  (equal?
   (call-with-input-file "source-root-fixture.json" read-json)
   "ready")
  (error "source-root relative fixture did not resolve"))

(displayln "gerbil-bazel source-root test")
