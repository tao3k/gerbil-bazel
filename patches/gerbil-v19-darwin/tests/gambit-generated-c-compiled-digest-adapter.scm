;; Exercise the compiled GSC digest through the existing standalone contracts.
(let ((external-single generation-file-sha)
      (external-many generation-file-digests)
      (selected (path-normalize
                  (string-append (getenv "GENERATION_BIN") "/gambit-file-sha256"))))
  (set! generation-file-sha
    (lambda (tool path)
      (if (equal? (path-normalize tool) selected)
          (c#generation-native-file-sha path)
          (external-single tool path))))
  (set! generation-file-digests
    (lambda (tool paths)
      (if (equal? (path-normalize tool) selected)
          (map (lambda (path) (list path (c#generation-native-file-sha path))) paths)
          (external-many tool paths)))))
