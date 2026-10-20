;; An execution-mode experiment, not a claim that transformer code is a loader.
(define (gxc#phi-source-code? code)
  (let loop ((pending (list code)) (fuel 131072))
    (cond
      ((null? pending) #t)
      ((<= fuel 0) #f)
      (else
        (let ((node (car pending)) (rest (cdr pending)))
          (cond
            ((not (pair? node)) (loop rest (- fuel 1)))
            ((memq (car node)
               '(c-lambda c-declare c-define c-define-type c-initialize include include-ci
                 ##c-lambda ##c-declare ##c-define ##c-define-type ##c-initialize ##c-code
                 ##inline-host-expression ##inline-host-statement)) #f)
            ((eq? (car node) 'quote)
             (and (pair? (cdr node)) (null? (cddr node))
                  (loop rest (- fuel 1))))
            (else (loop (cons (car node) (cons (cdr node) rest)) (- fuel 1)))))))))

(define (gxc#compile-generated-phi-source path code phi?)
  (if (and phi?
           (gxc#darwin-gnu-source-loader-platform?)
           (gxc#current-compile-static)
           (gxc#current-compile-invoke-gsc)
           (not (gxc#current-compile-debug))
           (gxc#phi-source-code? code))
      (begin
        (gxc#verbose "compile " path)
        (gxc#with-output-to-scheme-file path
          (lambda ()
            (display "#!gambit-generated-phi-source-v1\n")
            (pretty-print '(declare (block) (standard-bindings) (extended-bindings)
                                   (inlining-limit 200)))
            (pretty-print code)))
        (gxc#remove-loader-native-versions! path))
      (gxc#compile-scm-file__1 path code phi?)))
