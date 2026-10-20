;; Only a compiled, explicitly enabled Darwin backend replaces the digest calls.
(if (equal? (getenv "GAMBIT_GENERATED_C_IN_PROCESS_DIGESTS" #f) "1")
    (let ((external-single generation-file-sha)
          (external-many generation-file-digests)
          (selected (string-append (path-directory (path-normalize (executable-path)))
                                   "gambit-file-sha256")))
      (set! generation-file-sha
        (lambda (tool path)
          (if (equal? (path-normalize tool) selected)
              (generation-native-file-sha path)
              (external-single tool path))))
      (set! generation-file-digests
        (lambda (tool paths)
          (if (equal? (path-normalize tool) selected)
              (map (lambda (path) (list path (generation-native-file-sha path))) paths)
              (external-many tool paths))))))
