(import :std/encoding/json)
(def interfaces
  '("std/io/api.ssi" "std/format/format-string.ssi"
    "std/net/http/common/ioutil.ssi" "std/ffi.ssi" "std/serde/serialize.ssi"))
(for-each
 (lambda (name)
   (let* ((path (path-expand name (path-expand "lib" (getenv "GERBIL_HOME"))))
          (reference (map __AST->datum (read-syntax-from-file path))))
     (for-each
      (lambda (round)
        (let* ((started (time->seconds (current-time)))
               (forms (read-syntax-from-file path))
               (elapsed (- (time->seconds (current-time)) started)))
          (unless (and (= (length forms) (length reference))
                       (equal? (map __AST->datum forms) reference))
            (error "original SSI reader changed syntax datum" name))
          (displayln (json->string
                       (hash ("interface" name) ("round" round)
                             ("readSeconds" elapsed) ("forms" (length forms))
                             ("sameOriginalDatum" #t))))
          (force-output)))
      '(0 1 2))))
 interfaces)
(displayln "OK")
