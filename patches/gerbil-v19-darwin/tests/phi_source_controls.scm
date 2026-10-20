(define (check name value)
  (if value (begin (display "CASE-OK ") (display name) (newline) (force-output))
      (error "phi source control failed" name)))
(check "real Darwin GNU platform" (gxc#darwin-gnu-source-loader-platform?))
(check "ordinary transformer accepted"
  (gxc#phi-source-code? '(begin (define phi-control#transform (lambda (x) (cons x x))))))
(check "quoted foreign syntax is inert"
  (gxc#phi-source-code? '(begin (define phi-control#datum '(c-lambda () int "1")))))
(for-each
  (lambda (name)
    (check (string-append "foreign fallback:" (symbol->string name))
      (not (gxc#phi-source-code? `(begin (define x (,name () int "1")))))))
  '(c-lambda c-declare c-define c-define-type c-initialize include include-ci
    ##c-lambda ##c-declare ##c-define ##c-define-type ##c-initialize ##c-code
    ##inline-host-expression ##inline-host-statement))
(check "malformed quote rejected" (not (gxc#phi-source-code? '(quote x y))))
(let ((cycle (cons 'begin '())))
  (set-cdr! cycle cycle)
  (check "cyclic code rejected by bounded fuel" (not (gxc#phi-source-code? cycle))))
(define directory (getenv "PHI_CONTROL_DIRECTORY"))
(define source-path (string-append directory "/source.scm"))
(define native-path (string-append directory "/native.scm"))
(define debug-path (string-append directory "/debug.scm"))
(define code
  '(begin
     (define phi-control#transform
       (lambda (input)
         (let ((fresh (list input input)))
           (vector fresh (eq? (car fresh) (cadr fresh))
                   (call-with-values (lambda () (values input 'second)) list)))))
     (define phi-control#failure (lambda () (error "retained macro exception")))))
(define (compile-at path function debug?)
  (call-with-parameters
    (lambda () (function path code #t))
    gxc#current-compile-invoke-gsc #t
    gxc#current-compile-static #t
    gxc#current-compile-debug debug?
    gxc#current-compile-parallel #f))
(call-with-output-file (string-append directory "/source.o1")
  (lambda (port) (display "obsolete-native-version" port)))
(compile-at source-path gxc#compile-generated-phi-source #f)
(check "source emitted and old native removed"
  (and (file-exists? source-path) (not (file-exists? (string-append directory "/source.o1")))))
(define callback-observed #f)
(##load source-path
  (lambda (script resolved) (set! callback-observed (cons script resolved))) #t #t #f #t)
(check "explicit artifact tag and resolved file callback"
  (and (member (car callback-observed) '("gambit-generated-phi-source-v1" "gambit-compiled-phi-v1"))
       (equal? (cdr callback-observed) source-path)))
(load source-path)
(check "ordinary load uses generated Scheme protocol" (procedure? phi-control#transform))
(add-load-path! directory)
(load-module "source")
(check "real load-module uses generated Scheme protocol" (procedure? phi-control#transform))
(define unmarked-path (string-append directory "/ordinary.ss"))
(call-with-output-file unmarked-path
  (lambda (port) (display "(def ordinary-control 123)\n" port)))
(load unmarked-path)
(check "unmarked Gerbil source still expands" (= ordinary-control 123))
(define source-transform phi-control#transform)
(define source-failure phi-control#failure)
(define shared (list 'shared 'input))
(define source-result (source-transform shared))
(check "source execution preserves fresh result and alias"
  (and (vector-ref source-result 1) (eq? (caar (vector-ref source-result 2)) 'shared)
       (not (eq? (vector-ref source-result 0) (vector-ref (source-transform shared) 0)))))
(compile-at native-path gxc#compile-scm-file__1 #f)
(check "original path emits a native version" (file-exists? (string-append directory "/native.o1")))
(##load (string-append directory "/native.o1") (lambda args #f) #t #t #f #t)
(check "source and original native execution agree"
  (equal? source-result (phi-control#transform shared)))
(check "source exception preserved"
  (with-exception-catcher (lambda (error) #t) (lambda () (source-failure) #f)))
(check "native exception preserved"
  (with-exception-catcher (lambda (error) #t) (lambda () (phi-control#failure) #f)))
(compile-at debug-path gxc#compile-generated-phi-source #t)
(check "explicit debug retains native compilation" (file-exists? (string-append directory "/debug.o1")))
(##gc)
(check "source closure roots survive collection"
  (equal? source-result (source-transform shared)))
(display "OK") (newline) (force-output)
