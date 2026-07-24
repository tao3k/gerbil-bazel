#!/usr/bin/env gxi

;; Intentionally empty. The cache scenario exercises package action identity,
;; not a second compilation graph.
;; -*- Gerbil -*-

(import :std/build-script)

(defbuild-script
  '("src/value"))
