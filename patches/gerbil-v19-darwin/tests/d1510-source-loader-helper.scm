(define gxc#darwin-gnu-source-loader-platform?
  (c-lambda () bool
#<<c-end
#if defined(__APPLE__) && defined(__MACH__) && defined(__GNUC__) && !defined(__clang__)
___result = 1;
#else
___result = 0;
#endif
c-end
))

(define (gxc#load-only-code? code)
  (let ((fuel 4096))
    (define (pure? node)
      (set! fuel (- fuel 1))
      (and (> fuel 0)
           (pair? node)
           (cond
             ((eq? (car node) 'begin)
              (let loop ((rest (cdr node)))
                (cond ((null? rest) #t)
                      ((pair? rest) (and (pure? (car rest)) (loop (cdr rest))))
                      (else #f))))
             ((eq? (car node) 'load-module)
              (and (pair? (cdr node)) (string? (cadr node)) (null? (cddr node))))
             (else #f))))
    (pure? code)))

(define (gxc#remove-loader-native-versions! path)
  (let ((base (string-append (path-strip-extension path) ".o")))
    (let loop ((n 1))
      (let ((object (string-append base (number->string n))))
        (if (file-exists? object)
          (begin (delete-file object) (loop (+ n 1))))))))

(define (gxc#compile-generated-loader path code)
  (if (and (gxc#darwin-gnu-source-loader-platform?)
           (gxc#current-compile-static)
           (gxc#current-compile-invoke-gsc)
           (gxc#load-only-code? code))
    (begin
      (call-with-parameters
        (lambda () (gxc#compile-scm-file__0 path code))
        gxc#current-compile-invoke-gsc #f)
      (gxc#remove-loader-native-versions! path))
    (gxc#compile-scm-file__0 path code)))
