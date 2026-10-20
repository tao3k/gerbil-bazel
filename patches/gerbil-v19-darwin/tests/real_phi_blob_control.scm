(define (check name condition)
  (if condition
      (begin (display "CASE-OK ") (display name) (newline) (force-output))
      (error "real generated phi control failed" name)))
(define mode (getenv "REAL_PHI_MODE"))
(define source-path (getenv "REAL_PHI_SOURCE"))
(define blob-path (getenv "REAL_PHI_BLOB"))
(define module-dir (getenv "REAL_PHI_MODULE_DIR"))
(define target '|gerbil-mcp/util/strings[1]#_g184978_|)
(define (source-datum obj)
  (cond ((##source? obj) (source-datum (##source-code obj)))
        ((pair? obj) (cons (source-datum (car obj)) (source-datum (cdr obj))))
        (else obj)))
(define (uninitialized?)
  (##unbound? (##global-var-ref (##make-global-var target))))
(define (read-generated content name)
  (##call-with-input-string content
    (lambda (port)
      (##port-name-set! port name)
      (##read-all-as-a-begin-expr-from-port
       port (readtable-case-conversion?-set (##current-readtable) #f)
       ##wrap-datum ##unwrap-datum '() #f #f #t))))
(define (compile-source)
  (let* ((content (call-with-input-file source-path
                    (lambda (p) (read-line p #f))))
         (parsed (read-generated content source-path))
         (top-cte (##top-cte-clone ##interaction-cte)))
    (##call-with-values
     (lambda ()
       (##in-new-compilation-ctx '(c)
        (lambda () (##comp-top top-cte (vector-ref parsed 1) #f))))
     (lambda (code ctx)
       (##extract-demand-modules (##convert-source-to-locat! code) ctx)))))
(check "real phase globals initially unbound" (uninitialized?))
(cond
 ((string=? mode "inspect")
  (display "EXPLICIT-CASE-READ ")
  (write (source-datum (vector-ref
   (read-generated "(quote (Interface interface TypedDefinitions))" "case-control") 1)))
  (newline)
  (let* ((ctx (gx#import-module ':gerbil/core/contract))
         (binding (gx#resolve-identifier 'Interface 0 ctx)))
    (display "CONTRACT-CONTEXT ") (write (gx#module-context-id ctx)) (newline)
    (display "INTERFACE-BINDING ") (write binding) (newline)
    (display "INTERFACE-SYNTAX-BINDING ") (write (gx#syntax-binding? binding)) (newline)
    (when (gx#syntax-binding? binding)
      (display "INTERFACE-MODULE-CONTEXT ")
      (write (gx#module-context? (gx#syntax-binding-e binding))) (newline))))
 ((string=? mode "produce")
  (let* ((code (compile-source)) (bytes (##object->u8vector code)))
    (check "actual generated phase code serialized" (> (u8vector-length bytes) 0))
    (call-with-output-file blob-path
      (lambda (p) (write-subu8vector bytes 0 (u8vector-length bytes) p)))
    (call-with-output-file (path-expand "real-phase-control.scm" module-dir)
      (lambda (p)
        (write
         '(let ((bytes (make-u8vector
                       (file-info-size (file-info (getenv "REAL_PHI_BLOB"))))))
            (call-with-input-file (getenv "REAL_PHI_BLOB")
              (lambda (port)
                (if (not (= (read-subu8vector bytes 0 (u8vector-length bytes) port
                                              (u8vector-length bytes))
                            (u8vector-length bytes)))
                    (error "incomplete real phase blob"))))
            (##setup-requirements-and-run (##u8vector->object bytes) #f)) p)
        (newline p)))
    (check "producer did not initialize phase globals" (uninitialized?))))
 (else
  (gx#import-module ':gerbil/core/contract)
  (let ((started (time->seconds (current-time))) (before (##process-statistics)))
  (cond
   ((string=? mode "native") (load-module "gerbil-mcp/util/strings~1"))
   ((string=? mode "module")
      (begin
        (add-load-path! module-dir)
        (load-module "real-phase-control")))
   (else
      (let ((code
         (if (string=? mode "source") (compile-source)
             (let ((bytes (make-u8vector (file-info-size (file-info blob-path)))))
               (call-with-input-file blob-path
                 (lambda (p)
                   (check "whole actual phase blob read"
                     (= (read-subu8vector bytes 0 (u8vector-length bytes) p
                                         (u8vector-length bytes))
                        (u8vector-length bytes)))))
               (##u8vector->object bytes)))))
    (with-exception-catcher
     (lambda (exn)
       (display "PHASE-ERROR-IRRITANTS ")
       (write ((##eval 'error-irritants) exn))
       (newline) (force-output) (raise exn))
     (lambda () (##setup-requirements-and-run code #f))))))
  (let ((after (##process-statistics)))
    (display "PHASE-INIT-COST\t") (display mode) (display "\t")
    (display (- (time->seconds (current-time)) started)) (display "\t")
    (display (- (f64vector-ref after 7) (f64vector-ref before 7))) (newline)))
    (let ((phase-quote (##eval target)))
      (check "real phase syntax quote is initialized" (not (uninitialized?)))
      (check "real phase syntax datum retained"
        (eq? (gx#syntax-e phase-quote) 'with-dispatch-arguments))
      (check "real phase lexical marks retained"
        (pair? (gx#syntax-quote-marks phase-quote)))
      (##gc)
      (check "actual phase quote survives GC"
        (eq? (gx#syntax-e (##eval target)) 'with-dispatch-arguments))
      (when (string=? mode "module")
        (let ((order (module-load-order "real-phase-control")))
          (load-module "real-phase-control")
          (check "ordinary repeat load retains phase object identity"
            (eq? phase-quote (##eval target)))
          (check "ordinary repeat load retains module order"
            (= order (module-load-order "real-phase-control"))))))))
(display "OK") (newline) (force-output)
