#!/usr/bin/env gxi
(import :std/build-script)
(defbuild-script
  '("list/list-builder" "list/list"
    "encoding/json/env" "encoding/json/util"
    "encoding/json/reader" "encoding/json/writer"
    "encoding/json/io" "encoding/json/api")
  libdir: (path-expand "artifacts/lib" (path-directory (this-source-file)))
  verbose: #t)
