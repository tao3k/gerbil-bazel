(define (gxc#compile-generated-phi-source path code phi?)
  (if (and phi? (gxc#darwin-gnu-source-loader-platform?)
           (gxc#current-compile-static) (gxc#current-compile-invoke-gsc)
           (not (gxc#current-compile-debug)) (gxc#phi-source-code? code))
      (begin
        (gxc#verbose "compile " path)
        (let* ((content
                (call-with-output-string ""
                  (lambda (port)
                    (parameterize ((current-output-port port))
                      (pretty-print '(declare (block) (standard-bindings) (extended-bindings)
                                             (inlining-limit 200)))
                      (pretty-print code)))))
               (parsed (##read-all-as-a-begin-expr-from-string content path))
               (top-cte (##top-cte-clone ##interaction-cte))
               (compiled
                (##call-with-values
                  (lambda ()
                    (##in-new-compilation-ctx '(c)
                      (lambda () (##comp-top top-cte (vector-ref parsed 1) #f))))
                  (lambda (code ctx)
                    (##extract-demand-modules (##convert-source-to-locat! code) ctx))))
               (bytes (##object->u8vector compiled)))
          (gxc#with-output-to-scheme-file path
            (lambda ()
              (display "#!gambit-compiled-phi-v1\n")
              (force-output)
              (write-subu8vector bytes 0 (u8vector-length bytes) (current-output-port)))))
        (gxc#remove-loader-native-versions! path))
      (gxc#compile-scm-file__1 path code phi?)))
