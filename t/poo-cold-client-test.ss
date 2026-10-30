;;; Real package regression: empty prefix, complete owner build and native index.
(import (only-in :std/io/tempfile call-with-temporary-directory)
        (only-in :std/misc/process run-process/batch)
        (only-in :std/misc/ports read-all-as-string))

(def (require! value message) (unless value (error message)))
(call-with-temporary-directory "sdk-poo-cold"
  (lambda (prefix)
    (setenv "GERBIL_PATH" prefix)
    (require! (not (getenv "GERBIL_LOADPATH" #f)) "cold caller has a load-path override")
    (def repository "github.com/tao3k/gerbil-poo")
    (def package-root (path-expand repository (path-expand "pkg" prefix)))
    (def manifest (string-append package-root ".manifest"))
    (def tags (path-expand "pkg/TAGS" prefix))
    (require! (not (file-exists? (path-expand "lib" prefix))) "cold prefix has products")
    (require! (not (file-exists? manifest)) "cold prefix has a package manifest")
    ;; The immutable client is the actual Aitia cold regression, not a fixture.
    ;; The SDK CLI owns acquisition, every declared build target and the manifest.
    (run-process/batch
      (list "gxpkg" "install"
        "github.com/tao3k/gerbil-poo@6500bce55dbb2493ad385d261f3a9b106dfdab92"))
    (require! (file-exists? manifest) "native package manifest is missing")
    (require! (file-exists? (path-expand "bin/representation-main" prefix))
              "complete package executable is missing")
    (def index (call-with-input-file tags read-all-as-string))
    (require! (string-contains index (string-append package-root "/object.ss,"))
              "native tag index omitted the real object source")
    (require! (string-contains index ":clan/poo/object")
              "native tag index omitted the object module identity")
    (run-process/batch
      (list "gxi" "-:max-heap=2G,debug=q" "-e"
        "(import :clan/poo/object) (def value (.o answer: 42)) (unless (= (.get value answer) 42) (error \"compiled cold client mismatch\")) (displayln \"NATIVE-POO-COLD-CONSUMER-OK\")"))))
(displayln "NATIVE-POO-COLD-CLIENT-OK")
