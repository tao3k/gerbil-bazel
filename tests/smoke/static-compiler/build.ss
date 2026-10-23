#!/usr/bin/env gxi
(import :std/build-script)
;; An executable makes native std/make compile static runtime objects too.
(defbuild-script '((gxc: "library") (exe: "main")))
