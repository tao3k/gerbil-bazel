#!/usr/bin/env gxi

(import :dependency
        :independent)

(unless (eq? dependency-ready 'ready)
  (error "transitive project dependency did not resolve"))

(unless (eq? independent-ready 'ready)
  (error "independent project dependency did not resolve"))

(displayln "gerbil-bazel smoke test")
