;; Contract-only adapter. Native GSC integration must bind this code in its identity.
(load (getenv "GENERATION_NATIVE_DIGEST_MODULE"))
(let ((external-single generation-file-sha)
      (external-many generation-file-digests)
      (selected (path-normalize
                  (string-append (getenv "GENERATION_BIN") "/gambit-file-sha256"))))
  (set! generation-file-sha
    (lambda (tool path)
      (if (equal? (path-normalize tool) selected)
          (generation-native-file-sha path)
          (external-single tool path))))
  (set! generation-file-digests
    (lambda (tool paths)
      (if (equal? (path-normalize tool) selected)
          (map (lambda (path) (list path (generation-native-file-sha path))) paths)
          (external-many tool paths)))))
