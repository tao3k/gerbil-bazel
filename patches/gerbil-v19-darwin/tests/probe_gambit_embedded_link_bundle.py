#!/usr/bin/env python3
"""Check a Gambit-only bundle carrier with an unchanged native object list."""
import argparse
import csv
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import signal
import subprocess

from bazel_host_environment import build_environment
from gambit_host_coalescing import render as render_coalesced_hosts
from gambit_rest_registers import inject as inject_rest_registers


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--coalesce-original-hosts", action="store_true")
    parser.add_argument("--coalesce-kernel", action="store_true")
    parser.add_argument("--guarded-global-jumps", action="store_true")
    parser.add_argument("--local-return-guards", action="store_true")
    parser.add_argument("--cache-label-bases", action="store_true")
    parser.add_argument("--gen-entry-count", action="store_true")
    parser.add_argument("--vector-entry-guards", action="store_true")
    parser.add_argument("--guarded-leaf-clones", action="store_true")
    parser.add_argument("--internal-leaf-clones", action="store_true")
    parser.add_argument("--known-return-guards", action="store_true")
    parser.add_argument("--local-subroutine-clones", action="store_true")
    parser.add_argument("--defer-local-frames", action="store_true")
    parser.add_argument("--guarded-readonly-traces", action="store_true")
    parser.add_argument("--guarded-trace-polls", action="store_true")
    parser.add_argument("--guarded-trace-restart-polls", action="store_true")
    parser.add_argument("--guarded-trace-coalesce-polls", action="store_true")
    parser.add_argument("--guarded-trace-primitive-boundary", action="store_true")
    parser.add_argument("--guarded-trace-epoch-cache", action="store_true")
    parser.add_argument("--guarded-trace-inline-lookup", action="store_true")
    parser.add_argument("--guarded-trace-outline-lookup", action="store_true")
    parser.add_argument("--guarded-trace-outline-returns", action="store_true")
    parser.add_argument("--guarded-trace-lookup-return-branches", action="store_true")
    parser.add_argument("--parameter-entry-fastpath", action="store_true")
    parser.add_argument("--parameter-identity-return", action="store_true")
    parser.add_argument("--parameter-env-lookup", action="store_true")
    parser.add_argument("--bounded-primitive-entries", action="store_true")
    parser.add_argument("--rest-register-fastpath", action="store_true")
    args = parser.parse_args()
    if args.parameter_entry_fastpath and (not args.coalesce_original_hosts or
            (args.guarded_trace_epoch_cache and not args.parameter_identity_return)):
        parser.error("parameter entry requires original hosts and explicit identity/coherence mode for epochs")
    if args.parameter_identity_return and not args.parameter_entry_fastpath:
        parser.error("identity return requires guarded parameter entry")
    if args.parameter_env_lookup and not args.parameter_identity_return:
        parser.error("environment lookup requires identity/coherence mode")
    if args.bounded_primitive_entries and not args.coalesce_original_hosts:
        parser.error("bounded primitive entries require original host coalescing")
    if args.guarded_trace_polls and not args.guarded_readonly_traces:
        parser.error("trace polls require readonly traces")
    if args.guarded_trace_restart_polls and not args.guarded_trace_polls:
        parser.error("restart polls require trace polls")
    if args.guarded_trace_coalesce_polls and not args.guarded_trace_restart_polls:
        parser.error("coalesced polls require readonly restart")
    if args.guarded_trace_primitive_boundary and not args.guarded_readonly_traces:
        parser.error("primitive boundary requires readonly traces")
    if args.guarded_trace_epoch_cache and not (args.guarded_trace_coalesce_polls and args.guarded_trace_primitive_boundary):
        parser.error("epoch contract requires coalesced polls and primitive boundary")
    if args.guarded_trace_inline_lookup and (args.guarded_trace_epoch_cache or not args.guarded_trace_coalesce_polls or not args.guarded_trace_primitive_boundary):
        parser.error("inline lookup requires uncached coalesced primitive traces")
    if args.guarded_trace_outline_lookup and not args.guarded_trace_inline_lookup:
        parser.error("outlined lookup requires inline lookup")
    if args.guarded_trace_outline_returns and not (args.guarded_trace_outline_lookup and args.guarded_trace_lookup_return_branches):
        parser.error('return outlining requires outlined lookup and precise return branches')
    if args.guarded_trace_lookup_return_branches and not args.guarded_trace_inline_lookup:
        parser.error('lookup return branches require precise lookup fallback')
    if args.guarded_readonly_traces and (not args.coalesce_original_hosts or any((
            args.coalesce_kernel, args.guarded_global_jumps, args.local_return_guards,
            args.cache_label_bases, args.gen_entry_count, args.vector_entry_guards,
            args.guarded_leaf_clones, args.internal_leaf_clones, args.known_return_guards,
            args.local_subroutine_clones, args.rest_register_fastpath))):
        parser.error("readonly traces require their own original-host contract")
    if args.defer_local_frames and not args.local_subroutine_clones:
        parser.error("deferred frames require local-subroutine copies")
    if args.local_subroutine_clones and (not args.coalesce_original_hosts or args.known_return_guards or args.guarded_leaf_clones or args.gen_entry_count or args.vector_entry_guards):
        parser.error("local subroutine copies require an isolated original-host contract")
    if args.guarded_global_jumps and not args.coalesce_original_hosts:
        parser.error("guarded global jumps require host coalescing")
    if args.local_return_guards and not args.coalesce_original_hosts:
        parser.error("this local return carrier contract requires host coalescing")
    if args.cache_label_bases and not args.coalesce_original_hosts:
        parser.error("label base snapshots require the original host carrier")
    if args.gen_entry_count and not args.coalesce_original_hosts:
        parser.error("generic entry diagnostic requires host coalescing")
    if args.vector_entry_guards and (not args.coalesce_original_hosts or args.gen_entry_count):
        parser.error("vector guards require a separate noninstrumented coalesced contract")
    if args.guarded_leaf_clones and (not args.guarded_global_jumps or args.vector_entry_guards or args.gen_entry_count):
        parser.error("leaf clone contract requires guarded global coalescing")
    if args.internal_leaf_clones and not args.guarded_leaf_clones:
        parser.error("internal copies require the leaf clone contract")
    if args.known_return_guards and (not args.coalesce_original_hosts or args.guarded_leaf_clones or args.gen_entry_count or args.vector_entry_guards):
        parser.error("known returns require their own original-host contract")
    if args.coalesce_kernel and not args.coalesce_original_hosts:
        parser.error("kernel requires original host coalescing")
    if args.rest_register_fastpath and args.coalesce_original_hosts:
        parser.error("rest and coalescing contracts must stay separate")
    repo = Path(__file__).resolve().parents[3]
    output = args.output.resolve()
    home = args.source.resolve() / "build"
    if platform.system() != "Darwin" or not all(p.is_relative_to(repo / ".data") for p in (home, output)):
        parser.error("Darwin isolated source and evidence required")
    output.mkdir(parents=True, exist_ok=False)
    env = build_environment()
    env.update(GERBIL_HOME=str(home), GERBIL_PATH=str(output / "empty-user"),
               GERBIL_LOADPATH=str(home / "lib"), GERBIL_GSC=str(home / "bin/gsc"),
               GAMBOPT=f"~~bin={home / 'bin'},~~lib={home / 'lib'},~~include={home / 'include'}")
    cores = int(subprocess.check_output(["sysctl", "-n", "hw.physicalcpu"], text=True))
    macros = subprocess.check_output([env["CC"], "-dM", "-E", "-x", "c", os.devnull], env=env, text=True)
    if "#define __clang__" in macros or "#define __GNUC__ 16\n" not in macros:
        raise RuntimeError("real GNU GCC 16 required")
    report = {"qualified": False, "performanceQualified": False,
              "scope": "tiny-native-link-carrier-contract", "consumerObjectListChanged": False,
              "cores": cores,
              "gscSha256": hashlib.sha256((home / "bin/gsc").read_bytes()).hexdigest()}

    def run(name, command, child_env=None):
        with (output / f"{name}.log").open("w") as log:
            child = subprocess.Popen(command, env=child_env or env, stdout=log, stderr=subprocess.STDOUT,
                                     start_new_session=True)
            try:
                code = child.wait(timeout=120)
            finally:
                if child.poll() is None:
                    os.killpg(child.pid, signal.SIGTERM)
                    try:
                        child.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        os.killpg(child.pid, signal.SIGKILL)
                        child.wait()
            if code:
                raise subprocess.CalledProcessError(code, command)
        print(f"LINK-CONTRACT-OK {name}", flush=True)

    def compile_c(name, path):
        child_env = dict(env, GAMBITDIR_INCLUDE=str(home / "include"), GAMBITDIR_LIB=str(home / "lib"),
                         BUILD_OBJ_INPUT_FILENAMES_PARAM=str(path),
                         BUILD_OBJ_OUTPUT_FILENAME_PARAM=str(path.with_suffix(".o")),
                         BUILD_OBJ_META_INFO_FILE_PARAM=str(path))
        if args.coalesce_kernel and name == "compile-embedded-link":
            internal = args.source.resolve() / "src/gambit/lib"
            headers = args.source.resolve() / "src/gambit/include"
            child_env["BUILD_OBJ_CC_OPTIONS_PARAM"] = f'-DHAVE_CONFIG_H -I{internal} -I{headers}'
        run(name, [str(home / "bin/gambuild-C"), "obj"], child_env)

    try:
        sources = {
            "a": '(declare (extended-bindings) (standard-bindings))\n(##namespace ("alpha#" entry collect0 local-return))\n(define (entry n) (##gc) (+ n 1))\n(define (collect0 . args) (##gc) args)\n(define (local-return obj id) (+ (if (##structure-instance-of? obj id) 10 20) 1))\n(display "A-INIT\\n")\n',
            "b": '''(declare (extended-bindings) (standard-bindings))
(##namespace ("alpha#" entry) ("beta#" value exercise collect1 collect2))
(define (value) (entry 40))
(define (collect1 a . args) (##gc) (cons a args))
(define (collect2 a b . args) (##gc) (cons a (cons b args)))
(define (exercise)
  (let ((events '()))
    (let ((result
           (dynamic-wind
             (lambda () (set! events (cons 'before events)))
             (lambda ()
               (call-with-current-continuation (lambda (exit) (exit (entry 40)))))
             (lambda () (set! events (cons 'after events))))))
      (if (not (and (= result 41) (equal? events '(after before))))
          (error "lost continuation or wind state")))
    (call-with-values (lambda () (values (entry 40) (entry 41)))
                      (lambda (a b) (+ a b)))))
(display "B-INIT\\n")
''',
            "main": '''(declare (extended-bindings) (standard-bindings))
(##namespace ("alpha#" entry collect0 local-return) ("beta#" value exercise collect1 collect2))
(define (assert-result expected)
  (if (not (= (value) expected)) (error "wrong bundle result")))
(assert-result 41)
(let* ((root (##structure ##type-type 'root 'probe 26 #f '#()))
       (child (##structure ##type-type 'child 'probe 26 root '#()))
       (obj (##structure child)))
  (let loop ((n 200))
    (if (> n 0)
        (begin
          (if (not (and (= (local-return obj 'root) 11)
                        (= (local-return obj 'missing) 21)
                        (= (local-return 42 'root) 21)))
              (error "lost local continuation result"))
          (##gc)
          (loop (- n 1))))))
(let loop ((n 0) (args '()))
  (for-each
    (lambda (entry)
      (let ((required (car entry)) (proc (cdr entry)))
        (if (< n required)
            (if (not (with-exception-catcher (lambda (e) #t) (lambda () (apply proc args) #f)))
                (error "lost rest arity exception"))
            (let ((result (apply proc args)))
              (if (not (equal? result args)) (error "wrong rest argument order"))
              (if (and (> n 0) (eq? result args)) (error "rest list not freshly allocated"))))))
    (list (cons 0 collect0) (cons 1 collect1) (cons 2 collect2)))
  (if (< n 12) (loop (+ n 1) (cons n args))))
(if (not (= (exercise) 83)) (error "lost multiple values"))
(let ((threads (map (lambda (n) (make-thread (lambda () (thread-yield!) (value))))
                    '(0 1 2 3 4 5 6 7 8 9 10 11))))
  (for-each thread-start! threads)
  (for-each (lambda (thread)
              (if (not (= (thread-join! thread) 41)) (error "lost thread state")))
            threads))
(set! entry (lambda (n) (+ n 2)))
(assert-result 42)
(set! entry 'not-a-procedure)
(if (not (with-exception-catcher (lambda (e) #t) (lambda () (value) #f)))
    (error "lost non-procedure exception"))
(set! entry (lambda (n) (+ n 1)))
(let loop ((n 200))
  (if (> n 0) (begin (##gc) (assert-result 41) (loop (- n 1)))))
(for-each (lambda (name)
  (if (not (##lookup-registered-module name)) (error "lost module alias" name))) '(a b))
(display "EMBEDDED-LINK-OK\\n")
''',
        }
        if args.parameter_entry_fastpath:
            for name in ("b", "main"):
                sources[name] = sources[name].replace("exercise collect1 collect2)",
                    "exercise collect1 collect2 param-read param-value param-filter-calls)")
            sources["b"] += '''
(define param-filter-calls 0)
(define param-value
  (make-parameter 41 ##identity
    (lambda (x) (set! param-filter-calls (+ param-filter-calls 1)) (+ x 1))))
(define (param-read) (param-value))
'''
            sources["main"] += '''
(if (not (##parameter? param-value)) (error "parameter identity"))
(parameterize ((param-value 70))
  (let ((before param-filter-calls))
    (let loop ((n 300))
      (if (> n 0)
          (begin (if (not (= (param-read) 71)) (error "parameter filtered read"))
                 (loop (- n 1)))))
    (if (not (= (- param-filter-calls before) 300)) (error "getter effects skipped")))
  (param-value 80)
  (let ((q (make-parameter 2)) (r (make-parameter 3)))
    (parameterize ((q 12) (r 13))
      (param-read)
      (q)
      (if (not (= (param-read) 81)) (error "parameter cache second slot"))
      (q) (r)
      (if (not (= (param-read) 81)) (error "parameter cache third slot"))
      (let ((self (##closure-ref param-value 2)))
        (##closure-set! param-value 2 q)
        (if (not (= (param-read) 13)) (error "parameter captured self mutation"))
        (##closure-set! param-value 2 self))))
  (##gc)
  (if (not (= (param-read) 81)) (error "parameter setter GC"))
  (let ((save param-value))
    (set! param-value (lambda () 99))
    (if (not (= (param-read) 99)) (error "parameter global rebinding"))
    (set! param-value save))
  (parameterize ((param-value 90))
    (if (not (= (param-read) 91)) (error "nested parameter context"))))
(if (not (= (param-read) 42)) (error "parameter context restore"))
(let ((save param-value))
  (set! param-value (make-parameter 10 ##identity (lambda (x) (values x (+ x 1)))))
  (parameterize ((param-value 20))
    (call-with-values param-read
      (lambda (a b) (if (not (and (= a 20) (= b 21))) (error "getter multiple values")))))
  (set! param-value (make-parameter 10 ##identity (lambda (x) (error "getter exception"))))
  (parameterize ((param-value 20))
    (if (not (with-exception-catcher (lambda (e) #t) (lambda () (param-read) #f)))
        (error "getter exception dropped")))
  (set! param-value save))
(let ((threads
       (map (lambda (n) (make-thread (lambda ()
             (parameterize ((param-value n))
               (thread-yield!) (##gc)
               (if (not (= (param-read) (+ n 1))) (error "parameter thread state"))))))
            '(1 2 3 4 5 6 7 8 9 10 11 12))))
  (for-each thread-start! threads)
  (for-each thread-join! threads))
(display "PARAMETER-ENTRY-OK\\n")
'''
            sources["main"] = sources["main"].replace('(display "EMBEDDED-LINK-OK\\n")', '')
            sources["main"] += '(display "EMBEDDED-LINK-OK\\n")\n'
        if args.parameter_identity_return:
            namespace = '(##namespace ("beta#" param-default param-default-read))\n'
            sources['b'] += namespace + '''
(define param-default (make-parameter 41))
(define (param-default-read) (param-default))
'''
            sources['main'] += namespace + '''
(parameterize ((param-default 70))
  (let loop ((n 300))
    (if (> n 0)
        (begin
          (if (not (= (param-default-read) 70)) (error "identity getter result"))
          (if (= (modulo n 20) 0) (##gc))
          (loop (- n 1)))))
  (let* ((descr (##closure-ref param-default 1))
         (getter (##vector-ref descr 3))
         (effects 0))
    (##vector-set! descr 3
      (lambda (x) (set! effects (+ effects 1)) (values x (+ x 1))))
    (call-with-values param-default-read
      (lambda (a b)
        (if (not (and (= a 70) (= b 71))) (error "identity replacement values"))))
    (if (not (= effects 1)) (error "identity replacement effects"))
    (let* ((global (##make-global-var '##identity))
           (previous (##global-var-ref global))
           (replacement (lambda (x) (set! effects (+ effects 1)) (values x (+ x 2)))))
      (##global-var-set! global replacement)
      (##vector-set! descr 3 getter)
      (if (not (= (param-default-read) 70)) (error "captured original identity changed"))
      (if (not (= effects 1)) (error "mutable global used as identity guard"))
      (##vector-set! descr 3 replacement)
      (call-with-values param-default-read
        (lambda (a b)
          (if (not (and (= a 70) (= b 72))) (error "rebound identity getter values"))))
      (if (not (= effects 2)) (error "rebound identity getter skipped"))
      (##global-var-set! global previous))
    (##vector-set! descr 3 (lambda (x) (error "replacement getter")))
    (if (not (with-exception-catcher (lambda (e) #t) (lambda () (param-default-read) #f)))
        (error "identity replacement exception"))
    (##vector-set! descr 3 getter)
    (##gc)
    (if (not (= (param-default-read) 70)) (error "identity restored getter")))
  (param-default 80)
  (if (not (= (param-default-read) 80)) (error "identity setter"))
  (parameterize ((param-default 90))
    (if (not (= (param-default-read) 90)) (error "identity nested binding")))
  (if (not (= (param-default-read) 80)) (error "identity binding restoration")))
(if (not (= (param-default-read) 41)) (error "identity outer binding"))
(let ((threads
       (map (lambda (n) (make-thread (lambda ()
              (parameterize ((param-default n))
                (thread-yield!) (##gc)
                (if (not (= (param-default-read) n)) (error "identity thread binding"))))))
            '(1 2 3 4 5 6 7 8 9 10 11 12))))
  (for-each thread-start! threads)
  (for-each thread-join! threads))
(display "PARAMETER-IDENTITY-OK\\n")
'''
        if args.parameter_env_lookup:
            sources['main'] += '''
(param-default 85)
(if (not (= (param-default-read) 85)) (error "live unbound default setter"))
(param-default 41)
(let* ((saved param-default) (p (make-parameter 7))
       (a (make-parameter 1)) (b (make-parameter 2)) (c (make-parameter 3)))
  (for-each (lambda (param) (##vector-set! (##closure-ref param 1) 1 123)) (list p a b c))
  (set! param-default p)
  (parameterize ((p 70) (a 11) (b 12) (c 13))
    (a) (b) (c)
    (if (not (= (param-default-read) 70)) (error "uncached bound hash collision"))
    (p 80)
    (a) (b) (c)
    (if (not (= (param-default-read) 80)) (error "uncached bound setter"))
    (let* ((global (##make-global-var '##env-lookup))
           (previous (##global-var-ref global)) (effects 0))
      (##global-var-set! global
        (lambda (env param) (set! effects (+ effects 1)) (cons param 99)))
      (a) (b) (c)
      (let* ((before effects) (reference (p)) (delta (- effects before)))
        (a) (b) (c)
        (let ((before effects) (actual (param-default-read)))
          (if (not (and (= actual reference) (= (- effects before) delta)))
              (error "environment binding override bypassed"))))
      (##global-var-set! global previous)))
  (set! param-default saved))
(if (not (= (param-default-read) 41)) (error "environment global restoration"))
(display "PARAMETER-ENV-OK\\n")
'''
        if args.guarded_readonly_traces:
            for name in ("a", "main"):
                sources[name] = sources[name].replace("entry collect0 local-return)",
                    "entry collect0 local-return trace-route trace-methods)")
            sources["b"] = sources["b"].replace('(\"alpha#\" entry)',
                '(\"alpha#\" entry trace-route trace-methods)').replace(
                    "value exercise collect1 collect2)", "value exercise collect1 collect2 trace-cast)")
            sources["main"] = sources["main"].replace("value exercise collect1 collect2)",
                "value exercise collect1 collect2 trace-cast)")
            sources["a"] += '''
(define trace-methods
  (vector (lambda (obj)
            (declare (not safe) (not interrupts-enabled))
            (if (##structure? obj) obj (error "not an object")))))
(define (trace-route obj)
  (declare (not interrupts-enabled))
  (let ((proc (let () (declare (not safe)) (##vector-ref trace-methods 0))))
    (proc obj)))
'''
            sources["b"] += '''
(define (trace-cast obj tag)
  (declare (not interrupts-enabled))
  (let ((result (trace-route obj)))
    (if (let () (declare (not safe))
          (##eq? (##type-id (##structure-type result)) tag))
        obj
        (error "cast mismatch"))))
'''
            sources["main"] += '''
(let* ((type (##structure ##type-type 'trace-root 'probe 26 #f '#()))
       (other-type (##structure ##type-type 'trace-other 'probe 26 #f '#()))
       (obj (##structure type 41))
       (other (##structure other-type 42))
       (saved-route trace-route)
       (saved-method (vector-ref trace-methods 0)))
  (define (caught thunk)
    (with-exception-catcher (lambda (e) #t) (lambda () (thunk) #f)))
  (let warm ((n 200))
    (if (> n 0)
        (begin
          (if (not (eq? (trace-cast obj 'trace-root) obj)) (error "trace sustained identity"))
          (warm (- n 1)))))
  (let loop ((n 100))
    (if (> n 0)
        (begin
          (if (not (eq? (trace-cast obj 'trace-root) obj)) (error "trace identity"))
          (if (not (caught (lambda () (trace-cast obj 'trace-other)))) (error "trace cold error"))
          (##gc)
          (loop (- n 1)))))
  (##unchecked-structure-set! type 'trace-mutated 1 ##type-type #f)
  (if (not (eq? (trace-cast obj 'trace-mutated) obj)) (error "trace descriptor mutation"))
  (##unchecked-structure-set! type 'trace-root 1 ##type-type #f)
  (vector-set! trace-methods 0 (lambda (x) (##gc) other))
  (if (not (eq? (trace-cast obj 'trace-other) obj)) (error "trace vector mutation"))
  (vector-set! trace-methods 0 42)
  (if (not (caught (lambda () (trace-cast obj 'trace-root)))) (error "trace nonprocedure"))
  (vector-set! trace-methods 0 saved-method)
  (let ((calls 0))
    (set! trace-route (lambda (x) (set! calls (+ calls 1)) (##gc) other))
    (if (not (and (eq? (trace-cast obj 'trace-other) obj) (= calls 1)))
        (error "trace binding mutation or dropped effect")))
  (set! trace-route saved-route)
  (if (not (eq? (trace-cast obj 'trace-root) obj)) (error "trace restored binding")))
(display "TRACE-CONTRACT-OK\\n")
'''
            if args.guarded_trace_polls:
                for name in ("a", "b", "main"):
                    sources[name] = sources[name].replace("trace-route trace-methods)",
                                                          "trace-route trace-methods trace-bridge trace-bridge2)")
                sources["a"] += "\n(define (trace-bridge obj) (declare (interrupts-enabled)) (trace-bridge2 obj))\n(define (trace-bridge2 obj) (declare (interrupts-enabled)) (trace-route obj))\n"
                sources["b"] = sources["b"].replace("(result (trace-route obj))", "(result (trace-bridge obj))")
                marker = "(let* ((type (##structure ##type-type 'trace-root"
                hook = '''
(c-declare "unsigned long gb_trace_gc_callbacks; void gb_record_trace_gc(void) { ++gb_trace_gc_callbacks; }")
(define trace-record-gc (c-lambda () void "gb_record_trace_gc"))
(##interrupt-vector-set! 5 (lambda () (trace-record-gc) (##gc)))
'''
                sources["main"] = sources["main"].replace(marker, hook + marker)
            if args.guarded_trace_primitive_boundary:
                for name in ("b", "main"):
                    sources[name] = sources[name].replace("trace-cast)", "trace-cast trace-lookup trace-gct trace-ensure trace-rehashes)")
                sources["b"] += '''
(define trace-gct (##gc-hash-table-allocate 1024 16 '#f64(.45 .6363961030678927 .9)))
(define trace-rehashes 0)
(define (trace-ensure)
  (declare (not safe) (not interrupts-enabled))
  (if (##fx= 0 (##fxand (##unchecked-structure-ref trace-gct 1 #f #f) 32))
      trace-gct
      (let ((new (begin (set! trace-rehashes (+ trace-rehashes 1))
                        (##gc-hash-table-resize! trace-gct '#f64(.45 .6363961030678927 .9)))))
        (set! trace-gct (##gc-hash-table-rehash! trace-gct new))
        trace-gct)))
(define (trace-lookup obj)
  (declare (not safe) (not interrupts-enabled))
  (let ((table (trace-ensure))) (##gc-hash-table-ref table obj)))
'''
                sources["main"] = sources["main"].replace("  (let warm ((n 200))",
                    "  (##gc-hash-table-set! trace-gct obj obj)\n"
                    "  (vector-set! trace-methods 0 trace-lookup)\n  (let warm ((n 200))")
                sources["main"] = sources["main"].replace("  (##unchecked-structure-set! type 'trace-mutated",
                    "  (##unchecked-structure-set! trace-gct\n"
                    "    (##fxior (##unchecked-structure-ref trace-gct 1 #f #f) 32) 1 #f #f)\n"
                    "  (if (not (eq? (trace-cast obj 'trace-root) obj)) (error \"required rehash result\"))\n"
                    "  (if (<= trace-rehashes 0) (error \"required rehash was not exercised\"))\n"
                    "  (##unchecked-structure-set! type 'trace-mutated")
            if args.guarded_trace_lookup_return_branches:
                for name in ('a', 'b', 'main'):
                    sources[name] += '\n(##namespace ("alpha#" trace-loop-methods trace-loop-route trace-loop-bridge))\n'
                for name in ('b', 'main'):
                    sources[name] += '\n(##namespace ("beta#" trace-parent-lookup trace-loop-read trace-loop-unused trace-loop-kind?))\n'
                sources['a'] += '''
(define trace-loop-methods (vector (lambda (obj key) obj)))
(define (trace-loop-route obj key)
  (declare (not safe) (not interrupts-enabled))
  ((##vector-ref trace-loop-methods 0) obj key))
(define (trace-loop-bridge obj key)
  (declare (not safe) (not interrupts-enabled))
  (trace-loop-route obj key))
'''
                sources['b'] += '''
(define trace-loop-unused (##type-cast -14 (##type #f)))
(define (trace-loop-read obj key)
  (declare (not safe) (not interrupts-enabled))
  (##gc-hash-table-ref (##unchecked-structure-ref obj 1 #f #f) key))
(define (trace-loop-kind? obj)
  (declare (not safe))
  (if (##structure? obj)
      (let loop ((kind (##structure-type obj)))
        (if (not (##eq? (##type-id kind) 'lookup-loop-root))
            (let ((parent (##type-super kind)))
              (if parent (loop parent) #f))
            #t))
      #f))
(define (trace-parent-lookup obj)
  (declare (not safe))
  (let loop ((obj obj))
    (let ((value (trace-loop-bridge obj (##unchecked-structure-ref obj 2 #f #f))))
      (if (##eq? value trace-loop-unused)
          (if (trace-loop-kind? obj)
              (let ((next (##unchecked-structure-ref obj 3 #f #f)))
                (if next (loop next) #f))
              #f)
          value))))
'''
                sources['main'] += '''
(let* ((key (vector 'lookup-loop-key))
       (answer (vector 'lookup-loop-answer))
       (base-type (##structure ##type-type 'lookup-loop-root 'probe 26 #f '#()))
       (child-type (##structure ##type-type 'lookup-loop-child 'probe 26 base-type '#()))
       (leaf (##structure child-type (##gc-hash-table-allocate 1024 16 '#f64(.45 .6363961030678927 .9)) key #f))
       (middle (##structure child-type (##gc-hash-table-allocate 1024 16 '#f64(.45 .6363961030678927 .9)) key leaf))
       (root (##structure child-type (##gc-hash-table-allocate 1024 16 '#f64(.45 .6363961030678927 .9)) key middle)))
  (##vector-set! trace-loop-methods 0 trace-loop-read)
  (##gc-hash-table-set! (##unchecked-structure-ref leaf 1 #f #f) key answer)
  (let loop ((n 300))
    (if (##fx> n 0)
        (begin
          (if (not (eq? (trace-parent-lookup root) answer)) (error "lookup negative loop"))
          (if (##fx= (##fxmodulo n 20) 0) (##gc))
          (loop (##fx- n 1)))))
  (##gc-hash-table-set! (##unchecked-structure-ref leaf 1 #f #f) key #f)
  (if (trace-parent-lookup root) (error "lookup false value changed"))
  (##gc-hash-table-set! (##unchecked-structure-ref middle 1 #f #f) key answer)
  (if (not (eq? (trace-parent-lookup root) answer)) (error "lookup live insertion"))
  (##gc-hash-table-set! (##unchecked-structure-ref middle 1 #f #f) key trace-loop-unused)
  (##unchecked-structure-set! child-type #f 4 #f #f)
  (if (trace-parent-lookup root) (error "lookup mutable ancestor"))
  (##unchecked-structure-set! child-type base-type 4 #f #f)
  (if (trace-parent-lookup root) (error "lookup false leaf value"))
  (let build ((n 140) (kind base-type))
    (if (##fx> n 0)
        (build (##fx- n 1) (##structure ##type-type (vector n) 'deep 26 kind '#()))
        (begin
          (##unchecked-structure-set! root kind 0 #f #f)
          (##gc-hash-table-set! (##unchecked-structure-ref leaf 1 #f #f) key answer)
          (if (not (eq? (trace-parent-lookup root) answer)) (error "lookup deep ancestor fallback"))
          (##unchecked-structure-set! root child-type 0 #f #f))))
  (let ((calls 0) (saved (##vector-ref trace-loop-methods 0)))
    (##vector-set! trace-loop-methods 0 (lambda (obj key) (set! calls (+ calls 1)) answer))
    (if (not (and (eq? (trace-parent-lookup root) answer) (= calls 1)))
        (error "lookup overridden method"))
    (##vector-set! trace-loop-methods 0 saved)))
(display "LOOKUP-LOOP-OK\\n")
'''
            if args.guarded_trace_epoch_cache:
                for name in ("b", "main"):
                    sources[name] = sources[name].replace("trace-rehashes)", "trace-rehashes trace-batch trace-mutations)")
                sources["b"] += '''
(define (trace-batch obj)
  (declare (not safe))
  (let loop ((n 2000))
    (if (##fx> n 0)
        (begin
          (if (not (##eq? (trace-cast obj 'trace-root) obj)) (error "cache batch"))
          (loop (##fx- n 1))))))
(define (trace-mutations obj other)
  (trace-batch obj)
  (let ((saved (##vector-ref trace-methods 0)) (calls 0))
    (##vector-set! trace-methods 0 (lambda (x) (set! calls (##fx+ calls 1)) other))
    (if (not (and (##eq? (trace-cast obj 'trace-other) obj) (##fx= calls 1)))
        (error "same-host vector mutation"))
    (##vector-set! trace-methods 0 saved))
  (trace-batch obj)
  (let ((saved trace-ensure) (calls 0))
    (set! trace-ensure (lambda () (set! calls (##fx+ calls 1)) trace-gct))
    (if (not (and (##eq? (trace-cast obj 'trace-root) obj) (##fx= calls 1)))
        (error "same-host global mutation"))
    (set! trace-ensure saved))
  (trace-batch obj)
  (##gc-hash-table-set! trace-gct obj other)
  (if (not (##eq? (trace-cast obj 'trace-other) obj)) (error "cached lookup result"))
  (##gc-hash-table-set! trace-gct obj obj)
  (trace-batch obj)
  (let ((before trace-rehashes))
    (##unchecked-structure-set! trace-gct
      (##fxior (##unchecked-structure-ref trace-gct 1 #f #f) 32) 1 #f #f)
    (if (not (##eq? (trace-cast obj 'trace-root) obj)) (error "same-host required rehash"))
    (if (not (##fx> trace-rehashes before)) (error "cached mutable flags")))
  (trace-batch obj))
'''
                sources["main"] = sources["main"].replace("  (let warm ((n 200))", "  (trace-mutations obj other)\n  (let warm ((n 200))")
                if args.parameter_identity_return:
                    anchor = '(if (not (##eq? (trace-cast obj \'trace-root) obj)) (error "cache batch"))'
                    if sources['b'].count(anchor) != 1:
                        raise RuntimeError('cache/identity batch shape changed')
                    sources['b'] = sources['b'].replace(anchor, anchor + '''
          (if (not (##fx= (param-default-read) 41)) (error "cache identity interleave"))''')
                    sources['a'] += '''
(declare (not safe))
(##namespace ("alpha#" trace-thread-methods trace-thread-step))
(define trace-thread-methods
  (vector (lambda (thread expected ignored)
            (declare (not safe) (not interrupts-enabled))
            (if (##eq? (##unchecked-structure-ref thread 25 #f #f) expected)
                thread expected))))
(define (trace-thread-step thread expected)
  (declare (not safe) (not interrupts-enabled))
  (let ((proc (##vector-ref trace-thread-methods 0))) (proc thread expected 0)))
'''
                    sources['b'] += '''
(declare (not safe))
(##namespace ("alpha#" trace-thread-step)
             ("beta#" trace-thread-slot trace-thread-contract thread-p thread-q thread-r
                       thread-read-p thread-read-q thread-read-r))
(define (trace-thread-slot thread expected)
  (declare (not interrupts-enabled))
  (trace-thread-step thread expected))
(define thread-p (make-parameter 111))
(define thread-q (make-parameter 222))
(define thread-r (make-parameter 333))
(define (thread-read-p) (thread-p))
(define (thread-read-q) (thread-q))
(define (thread-read-r) (thread-r))
(define (trace-thread-contract thread)
  (parameterize ((thread-p 11) (thread-q 22) (thread-r 33))
    (let ((old (##unchecked-structure-ref thread 25 #f #f)))
     (let loop ((n 300))
      (if (> n 0)
          (begin
            (thread-read-p)
            (if (not (##eq? (trace-thread-slot thread old)
                           (if (##eq? (##unchecked-structure-ref thread 25 #f #f) old) thread old)))
                (error "cached thread slot after p"))
            (thread-read-q)
            (if (not (##eq? (trace-thread-slot thread old)
                           (if (##eq? (##unchecked-structure-ref thread 25 #f #f) old) thread old)))
                (error "cached thread slot after q"))
            (thread-read-r)
            (if (not (##eq? (trace-thread-slot thread old)
                           (if (##eq? (##unchecked-structure-ref thread 25 #f #f) old) thread old)))
                (error "cached thread slot after r"))
            (loop (- n 1))))))))
'''
                    sources['main'] += '''
(##namespace ("beta#" trace-thread-contract))
(trace-thread-contract (current-thread))
'''
        if args.gen_entry_count or args.vector_entry_guards:
            sources["b"] = sources["b"].replace("value exercise collect1 collect2)", "value exercise collect1 collect2 dispatch factory)")
            sources["b"] += "\n(define (dispatch proc n) (proc n))\n(define factory (let ((captured (vector 40))) (lambda (n) (##gc) (+ n (vector-ref captured 0)))))\n"
            sources["main"] = sources["main"].replace("value exercise collect1 collect2)", "value exercise collect1 collect2 dispatch factory)")
            sources["main"] += '''
(if (not (= (dispatch entry 40) 41)) (error "lost generic module call"))
(if (not (= (dispatch factory 2) 42)) (error "lost generic internal closure"))
(let* ((captured (vector 40)) (proc (lambda (n) (##gc) (+ n (vector-ref captured 0)))))
  (if (not (= (dispatch proc 2) 42)) (error "lost generic closure environment"))
  (vector-set! captured 0 50)
  (if (not (= (dispatch proc 2) 52)) (error "lost mutable closure environment")))
(if (not (with-exception-catcher (lambda (e) #t) (lambda () (dispatch 42 0) #f)))
    (error "lost generic nonprocedure exception"))
'''
        if args.vector_entry_guards:
            for name in ("b", "main"):
                sources[name] = sources[name].replace("dispatch factory)", "dispatch factory dispatch-vector dispatch-vector-call)")
            sources["b"] += "\n(define dispatch-vector (vector factory))\n(define (dispatch-vector-call n) (declare (not interrupts-enabled)) (let ((proc (let () (declare (not safe)) (##vector-ref dispatch-vector 0)))) (proc n)))\n"
            sources["main"] += '''
(if (not (= (dispatch-vector-call 2) 42)) (error "lost guarded vector closure"))
(vector-set! dispatch-vector 0 entry)
(if (not (= (dispatch-vector-call 40) 41)) (error "lost vector mutation fallback"))
(vector-set! dispatch-vector 0 42)
(if (not (with-exception-catcher (lambda (e) #t) (lambda () (dispatch-vector-call 0) #f)))
    (error "lost vector nonprocedure fallback"))
'''
        if args.guarded_leaf_clones or args.known_return_guards or args.local_subroutine_clones:
            sources["a"] = sources["a"].replace("entry collect0 local-return)", "entry collect0 local-return type-probe)")
            sources["a"] = sources["a"].replace("(declare (extended-bindings)", "(declare (block) (extended-bindings)")
            sources["a"] += "\n(define (type-probe obj) (##structure-instance-of? obj 'root))\n"
            sources["b"] = sources["b"].replace('("alpha#" entry)', '("alpha#" entry type-probe)').replace("value exercise collect1 collect2)", "value exercise collect1 collect2 probe-forward)")
            sources["b"] += "\n(define (probe-forward obj) (if (type-probe obj) 11 21))\n"
            sources["main"] = sources["main"].replace("value exercise collect1 collect2)", "value exercise collect1 collect2 probe-forward)")
            sources["main"] = sources["main"].replace("entry collect0 local-return)", "entry collect0 local-return type-probe)")
            sources["main"] += '''
(let* ((root (##structure ##type-type 'root 'probe 26 #f '#()))
       (child (##structure ##type-type 'child 'probe 26 root '#()))
       (obj (##structure child)))
  (if (not (and (= (probe-forward obj) 11) (= (probe-forward 42) 21)))
      (error "lost cloned predicate result"))
  (##unchecked-structure-set! root 'missing 1 ##type-type #f)
  (if (not (= (probe-forward obj) 21)) (error "cloned predicate cached mutable type")))
(let* ((cycle (##structure ##type-type 'cycle 'probe 26 #f '#()))
       (obj (##structure cycle))
       (worker (make-thread (lambda () (thread-sleep! 0.01) (##gc)
                             (##unchecked-structure-set! cycle #f 4 ##type-type #f)))))
  (##unchecked-structure-set! cycle cycle 4 ##type-type #f)
  (thread-start! worker)
  (if (not (= (probe-forward obj) 21)) (error "lost cloned cyclic poll"))
  (thread-join! worker))
(set! type-probe (lambda (obj) (##gc) #t))
(if (not (= (probe-forward 42) 11)) (error "lost cloned global rebinding fallback"))
(set! type-probe 42)
(if (not (with-exception-catcher (lambda (e) #t) (lambda () (probe-forward 42) #f)))
    (error "lost cloned global nonprocedure exception"))
'''
        if args.internal_leaf_clones or args.known_return_guards or args.local_subroutine_clones:
            sources["a"] = sources["a"].replace("local-return type-probe)", "local-return type-probe probe-internal)")
            sources["a"] = sources["a"].replace("(declare (block)", "(declare (block) (inlining-limit 0)")
            sources["a"] += "\n(define (probe-internal obj offset) (+ offset (if (type-probe obj) 11 21)))\n"
            sources["main"] = sources["main"].replace("local-return type-probe)", "local-return type-probe probe-internal)")
            sources["main"] += '''
(let* ((root (##structure ##type-type 'root 'probe 26 #f '#()))
       (obj (##structure root)))
  (if (not (and (= (probe-internal obj 10) 21) (= (probe-internal 42 10) 31)))
      (error "internal clone changed argument-count or binding semantics")))
'''
        if args.known_return_guards or args.local_subroutine_clones:
            for name in ("a", "main"):
                sources[name] = sources[name].replace("type-probe probe-internal)", "type-probe probe-internal micro-probe)")
            sources["a"] += "\n(define (micro-probe obj offset) (declare (not safe) (not interrupts-enabled)) (if (##structure-instance-of? obj 'root) (+ offset 11) (+ offset 21)))\n"
            sources["main"] += '''
(let* ((root (##structure ##type-type 'root 'probe 26 #f '#()))
       (missing (##structure ##type-type 'missing 'probe 26 #f '#()))
       (obj (##structure root)))
  (if (not (and (= (micro-probe obj 10) 21) (= (micro-probe 42 10) 31)
                (= (micro-probe (##structure missing) 10) 31)))
      (error "lost local type-subroutine return")))
'''
        if args.defer_local_frames:
            for name in ("a", "main"):
                sources[name] = sources[name].replace("probe-internal micro-probe)", "probe-internal micro-probe frame-probe)")
            sources["a"] += '''
(define (frame-cold klass) (##gc) (##structure klass))
(define (frame-probe obj)
  (declare (not safe) (not interrupts-enabled))
  (let ((klass (##structure-type obj)))
    (if (##structure-instance-of? klass 'root) klass (frame-cold klass))))
'''
            sources["main"] += '''
(let* ((meta (##structure ##type-type 'root 'probe 26 #f '#()))
       (other (##structure ##type-type 'missing 'probe 26 #f '#()))
       (klass (##structure meta))
       (cold (##structure other)))
  (let loop ((n 100))
    (if (> n 0)
        (begin
          (if (not (and (eq? (frame-probe (##structure klass)) klass)
                        (eq? (##structure-type (frame-probe (##structure cold))) cold)))
              (error "lost deferred frame root or cold GC continuation"))
          (##gc)
          (loop (- n 1))))))
'''
        if args.bounded_primitive_entries:
            sources['b'] += '''
(##namespace ("beta#" bounded-length bounded-reverse bounded-instance bounded-direct bounded-type-methods))
(define (bounded-length xs) (##length xs))
(define (bounded-reverse xs) (##reverse xs))
(define bounded-type-methods (vector ##structure-instance-of? ##structure-direct-instance-of?))
(define (bounded-instance obj id) ((vector-ref bounded-type-methods 0) obj id))
(define (bounded-direct obj id) ((vector-ref bounded-type-methods 1) obj id))
'''
            sources['main'] += '''
(##namespace ("beta#" bounded-length bounded-reverse bounded-instance bounded-direct bounded-type-methods))
(let repeat ((round 3))
  (if (> round 0)
      (begin
        (let loop ((size 0) (xs '()))
          (let ((result (bounded-reverse xs)))
            (if (not (= (bounded-length xs) size)) (error "bounded length"))
            (if (not (equal? result (reverse xs))) (error "bounded reverse"))
            (if (and (> size 0) (eq? result xs)) (error "reverse reused input pair"))
            (let compare ((left result) (right (reverse xs)))
              (if (pair? left)
                  (begin
                    (if (not (eq? (car left) (car right))) (error "reverse copied element"))
                    (compare (cdr left) (cdr right)))))
            (if (= (modulo size 7) 0) (##gc)))
          (if (< size 70) (loop (+ size 1) (cons (vector size) xs))))
        (repeat (- round 1)))))
(if (not (= (bounded-length '(1 2 . 3)) 2)) (error "private improper length fallback"))
(if (not (equal? (bounded-reverse '(1 2 . 3)) '(2 1))) (error "private improper reverse fallback"))
(let* ((root (##structure ##type-type 'bounded-root 'probe 26 #f '#()))
       (child (##structure ##type-type 'bounded-child 'probe 26 root '#()))
       (obj (##structure child 42)))
  (let loop ((n 300))
    (if (> n 0)
        (begin
          (if (not (and (bounded-instance obj 'bounded-root)
                        (bounded-instance obj 'bounded-child)
                        (bounded-direct obj 'bounded-child)
                        (not (bounded-direct obj 'bounded-root))
                        (not (bounded-instance obj 'missing))
                        (not (bounded-instance 42 'bounded-root))))
              (error "bounded live type hierarchy"))
          (if (= (modulo n 20) 0) (##gc))
          (loop (- n 1)))))
  (##unchecked-structure-set! child #f 4 #f #f)
  (if (bounded-instance obj 'bounded-root) (error "stale super type"))
  (##unchecked-structure-set! child root 4 #f #f)
  (##unchecked-structure-set! root 'bounded-mutated 1 #f #f)
  (if (not (and (bounded-instance obj 'bounded-mutated)
                (not (bounded-instance obj 'bounded-root))))
      (error "stale type identity")))
(let ((saved (vector-ref bounded-type-methods 0)) (effects 0))
  (vector-set! bounded-type-methods 0 (lambda (obj id) (set! effects (+ effects 1)) 'changed))
  (if (not (and (eq? (bounded-instance 42 'ignored) 'changed) (= effects 1)))
      (error "bounded indirect rebinding"))
  (vector-set! bounded-type-methods 0 saved))
(display "BOUNDED-PRIMITIVE-OK\\n")
'''
        for name, text in sources.items():
            scm = output / f"{name}.scm"
            scm.write_text(text)
            run(f"generate-{name}", [str(home / "bin/gsc"), "-c", "-o", str(scm.with_suffix(".c")), str(scm)])
            compile_c(f"compile-{name}", scm.with_suffix(".c"))
        objects = [output / f"{name}.o" for name in sources]
        original_link = output / "original-link.c"
        run("generate-original-link", [str(home / "bin/gsc"), "-link", "-o", str(original_link),
                                       *map(str, [output / f"{name}.c" for name in sources])])
        compile_c("compile-original-link", original_link)
        original_binary = output / "original-contract"
        run("original-native-link", [env["CC"], "-o", str(original_binary), *map(str, objects),
                                     str(original_link.with_suffix(".o")), f"-L{home / 'lib'}", "-lgambit", "-ldl", "-lm"])
        run("original-native-contract", [str(original_binary)])
        expected = "A-INIT\nB-INIT\nEMBEDDED-LINK-OK\n"
        if args.parameter_entry_fastpath:
            expected = "A-INIT\nB-INIT\nPARAMETER-ENTRY-OK\nEMBEDDED-LINK-OK\n"
        if args.parameter_identity_return:
            expected += "PARAMETER-IDENTITY-OK\n"
        if args.parameter_env_lookup:
            expected += "PARAMETER-ENV-OK\n"
        if args.guarded_readonly_traces:
            expected += "TRACE-CONTRACT-OK\n"
        if args.guarded_trace_lookup_return_branches:
            expected += 'LOOKUP-LOOP-OK\n'
        if args.bounded_primitive_entries:
            expected += "BOUNDED-PRIMITIVE-OK\n"
        if (output / "original-native-contract.log").read_text() != expected:
            raise RuntimeError("original contract failed before bundle comparison")
        if args.rest_register_fastpath:
            header = output / "gambit-rest-register-fastpath.h"
            header.write_bytes(Path(__file__).with_name(header.name).read_bytes())
            report["restRegisterHeaderSha256"] = hashlib.sha256(header.read_bytes()).hexdigest()
            report["restRegisterCallsites"] = {}
            for name in ("a", "b"):
                path = output / f"{name}.c"
                content, count = inject_rest_registers(path.read_text(), header)
                path.write_text(content)
                report["restRegisterCallsites"][name] = count
                compile_c(f"compile-rest-{name}", path)
        bundle = output / "gbbundle.scm"
        bundle.write_text('(##supply-module a)\n(##supply-module b)\n(##supply-module gbbundle)\n' +
                          "\n".join(f'(include {json.dumps(str(output / (name + ".scm")))})' for name in ("a", "b")) + "\n")
        cfile = bundle.with_suffix(".c")
        run("generate-bundle", [str(home / "bin/gsc"), "-c", "-o", str(cfile), str(bundle)])
        link = output / "link.c"
        run("generate-link", [str(home / "bin/gsc"), "-link", "-o", str(link),
                              str(output / "a.c"), str(output / "b.c"), str(cfile), str(output / "main.c")])
        link_content = link.read_text()
        for name in ("a", "b"):
            entry = f"___DEF_LNK(___LNK_{name})"
            lines = link_content.splitlines(keepends=True)
            matches = [line for line in lines if line.lstrip(",").strip() == entry]
            if len(matches) != 1:
                raise RuntimeError("original preload entry is not unique")
            link_content = "".join(line for line in lines if line not in matches)
        before, boundary, rest = link_content.partition("___BEGIN_LNK\n")
        entries, ending, after = rest.partition("___END_LNK")
        if not boundary or not ending:
            raise RuntimeError("replacement module initialization boundary differs")
        entries = [line.strip().lstrip(",") for line in entries.splitlines() if line.strip()]
        link_content = before + boundary + " " + "\n,".join(entries) + "\n" + ending + after

        content = cfile.read_text()
        controls = set(re.findall(r"^#define\s+([A-Za-z_]\w*)", content, re.MULTILINE))
        private = set(re.findall(r"\b___X\d+\b", content)) | {
            "___lp", "___lbltbl", "___symtbl", "___keytbl", "___cnstbl", "___subtbl", "___ofdtbl",
            "___glotbl", "___sym_names", "___key_names", "___glo_names", "___setup_mod", "___init_mod", "___module_descr"}
        # Header table selectors depend on the first translation unit's counts.
        selectors = {"___GLOTBL": "0,0,0,0", "___SYMTBL": "___symtbl,___SYMCOUNT,0",
                     "___KEYTBL": "___keytbl,___KEYCOUNT,0", "___LBLTBL": "&___lp,___lbltbl,___LBLCOUNT",
                     "___CNSTBL": "___cnstbl,___CNSCOUNT", "___SUBTBL": "___subtbl,___SUBCOUNT",
                     "___OFDTBL": "___ofdtbl,sizeof(___ofdtbl)/sizeof(___WORD)"}
        counts = {name: int(value) for name, value in re.findall(r"^#define\s+(___\w+COUNT)\s+(\d+)$", content, re.MULTILINE)}
        for table, count in (("___SYMTBL", "___SYMCOUNT"), ("___KEYTBL", "___KEYCOUNT"),
                             ("___CNSTBL", "___CNSCOUNT"), ("___SUBTBL", "___SUBCOUNT"), ("___OFDTBL", "___OFDCOUNT")):
            if not counts.get(count):
                selectors[table] = "0,0,0"
                if table not in ("___SYMTBL", "___KEYTBL"):
                    selectors[table] = "0,0"
        names = sorted(controls | private | set(selectors))
        wrapper = "\n".join(f'#pragma push_macro("{name}")\n#undef {name}' for name in names) + "\n"
        wrapper += "\n".join(f"#define {name} gb_embedded{name}" for name in sorted(private)) + "\n"
        wrapper += "\n".join(f"#define {name} {value}" for name, value in selectors.items()) + "\n"
        wrapper += "___LOCAL ___WORD ___lp;\n"
        wrapper += f'#include {json.dumps(str(cfile))}\n'
        wrapper += "\n".join(f'#pragma pop_macro("{name}")' for name in reversed(names)) + "\n"
        link.write_text(link_content + "\n" + wrapper)
        if args.rest_register_fastpath:
            link.write_text(original_link.read_text())
            report["scope"] = "tiny-native-rest-register-contract"
        if args.coalesce_original_hosts:
            paths = [output / "a.c", output / "b.c"]
            runtime_linkers = ()
            if args.coalesce_kernel:
                paths.insert(0, args.source.resolve() / "src/gambit/lib/_kernel.c")
                runtime_linkers = ("___LNK___kernel",)
            coalesced, details = render_coalesced_hosts(paths, original_link.read_text(), output, runtime_linkers,
                                                      args.guarded_global_jumps, local_return_guards=args.local_return_guards,
                                                      cache_label_bases=args.cache_label_bases,
                                                      gen_entry_count=args.gen_entry_count,
                                                      vector_entry_guards=args.vector_entry_guards,
                                                      guarded_leaf_clones=args.guarded_leaf_clones,
                                                      internal_leaf_clones=args.internal_leaf_clones,
                                                      known_return_guards=args.known_return_guards,
                                                      local_subroutine_clones=args.local_subroutine_clones,
                                                      defer_local_frames=args.defer_local_frames,
                                                      guarded_readonly_traces=args.guarded_readonly_traces,
                                                      guarded_trace_polls=args.guarded_trace_polls,
                                                      guarded_trace_restart_polls=args.guarded_trace_restart_polls,
                                                      guarded_trace_coalesce_polls=args.guarded_trace_coalesce_polls,
                                                      guarded_trace_primitive_boundary=args.guarded_trace_primitive_boundary,
                                                      guarded_trace_epoch_cache=args.guarded_trace_epoch_cache,
                                                      guarded_trace_inline_lookup=args.guarded_trace_inline_lookup,
                                                      guarded_trace_outline_lookup=args.guarded_trace_outline_lookup,
                                                      guarded_trace_outline_returns=args.guarded_trace_outline_returns,
                                                      guarded_trace_lookup_return_branches=args.guarded_trace_lookup_return_branches,
                                                      parameter_entry_fastpath=args.parameter_entry_fastpath,
                                                      parameter_identity_return=args.parameter_identity_return,
                                                      parameter_env_lookup=args.parameter_env_lookup,
                                                      bounded_primitive_entries=args.bounded_primitive_entries)
            if args.parameter_entry_fastpath:
                if not any(row["sites"] for row in details["parameterEntrySites"]):
                    raise RuntimeError("parameter entry lacks static sites")
                coalesced = '''#include <stdio.h>
static unsigned long gb_parameter_hits;
static unsigned long gb_parameter_slots[4];
#define GB_PARAMETER_HIT() (++gb_parameter_hits)
#define GB_PARAMETER_SLOT(slot) (++gb_parameter_slots[slot])
static void __attribute__((destructor)) gb_parameter_dump(void) {
  fprintf(stderr,"PARAMETER-HITS %lu\\n",gb_parameter_hits);
  fprintf(stderr,"PARAMETER-SLOTS %lu %lu %lu\\n",gb_parameter_slots[1],gb_parameter_slots[2],gb_parameter_slots[3]);
}
''' + coalesced
                if args.parameter_identity_return:
                    coalesced = '''#include <stdio.h>
static unsigned long gb_parameter_identity_hits;
#define GB_PARAMETER_IDENTITY_HIT() (++gb_parameter_identity_hits)
static void __attribute__((destructor)) gb_parameter_identity_dump(void) {
  fprintf(stderr,"PARAMETER-IDENTITY-HITS %lu\\n",gb_parameter_identity_hits);
}
''' + coalesced
                if args.parameter_env_lookup:
                    coalesced = '''#include <stdio.h>
static unsigned long gb_parameter_env_hits[2];
#define GB_PARAMETER_ENV_HIT(bound) (++gb_parameter_env_hits[bound])
static void __attribute__((destructor)) gb_parameter_env_dump(void) {
  fprintf(stderr,"PARAMETER-ENV-HITS %lu %lu\\n",gb_parameter_env_hits[0],gb_parameter_env_hits[1]);
}
''' + coalesced
            if args.guarded_readonly_traces:
                if not details.get("guardedReadOnlyTraces"):
                    raise RuntimeError("readonly trace contract has no actual static coverage")
                if args.guarded_trace_lookup_return_branches:
                    if not any(site['terminal'] == 'GB_ORIGINAL_REENTRY' for site in details['guardedReadOnlyTraces']):
                        raise RuntimeError('lookup loop contract must contain actual native reentry')
                    if not any(site['loweredTypeChainLoops'] for site in details['guardedReadOnlyTraces']):
                        raise RuntimeError('lookup loop must lower an actual original ancestor loop')
                    coalesced = '''#include <stdio.h>
static unsigned long gb_lookup_reentries;
#define GB_TRACE_REENTRY_EVENT(site) (++gb_lookup_reentries)
static void __attribute__((destructor)) gb_lookup_loop_dump(void) {
  fprintf(stderr,"TRACE-REENTRY-HITS %lu\\n",gb_lookup_reentries);
}
''' + coalesced
                if args.guarded_trace_epoch_cache:
                    if not any(site["epochCachedPrefix"] for site in details["guardedReadOnlyTraces"]):
                        raise RuntimeError("epoch contract has no cacheable prefix")
                    if args.parameter_identity_return:
                        if ('gb_slot->thread_sensitive=(1);' not in coalesced or
                            not re.search(r'gb_t\d+=\(___UNCHECKEDSTRUCTUREREF\([^;\n]+___FIX\(25L\)', coalesced)):
                            raise RuntimeError("thread epoch contract must cache an actual slot-25 read")
                    coalesced = '''#include <stdio.h>
static unsigned long gb_cache_hits;
#define GB_TRACE_CACHE_HIT() (++gb_cache_hits)
static void __attribute__((destructor)) gb_cache_dump(void) {
  fprintf(stderr,"TRACE-CACHE-HITS %lu\\n",gb_cache_hits);
}
''' + coalesced
                if args.guarded_trace_primitive_boundary:
                    effect_sites = [i for i, site in enumerate(details["guardedReadOnlyTraces"])
                                    if site["terminal"] == "GB_ORIGINAL_EFFECT" or site["inlinedLookups"]]
                    if not effect_sites:
                        raise RuntimeError("primitive contract must cover actual cross-module handoff")
                    counters = ",".join(f"[{i}]=1" for i in effect_sites)
                    coalesced = f'''#include <stdio.h>
static const unsigned char gb_effect_sites[256]={{{counters}}};
static unsigned long gb_effect_hits;
#define GB_TRACE_EFFECT_EVENT(site) (gb_effect_hits+=gb_effect_sites[site])
static void __attribute__((destructor)) gb_trace_effect_dump(void) {{
  fprintf(stderr,"TRACE-EFFECT-HITS %lu\\n",gb_effect_hits);
}}
''' + coalesced
                if args.guarded_trace_polls:
                    if not any(site["polls"] for site in details["guardedReadOnlyTraces"]):
                        raise RuntimeError("poll contract has no actual checkpoint coverage")
                    if not any(site["polls"] >= 2 and (site["terminal"].startswith("JUMPGEN") or
                               site["terminal"] in {"GB_ORIGINAL_EFFECT", "GB_ORIGINAL_RETURN", "GB_ORIGINAL_REENTRY", "GB_ORIGINAL_RET_TO"})
                               for site in details["guardedReadOnlyTraces"]):
                        raise RuntimeError("poll contract must cover original generic-method handoff")
                    coalesced = '''#include <stdio.h>
extern unsigned long gb_trace_gc_callbacks;
static unsigned long gb_trace_checks, gb_trace_forced;
#define GB_TRACE_POLL_EVENT() do { if ((++gb_trace_checks % 20) == 1) { ++gb_trace_forced; ___EXT(___raise_interrupt_pstate)(___ps,___INTR_OTHER); } } while (0)
static void __attribute__((destructor)) gb_trace_poll_dump(void) {
  fprintf(stderr,"TRACE-POLL-COUNTS %lu %lu %lu\\n",gb_trace_checks,gb_trace_forced,gb_trace_gc_callbacks);
}
''' + coalesced
                coalesced = '''#include <stdio.h>
static unsigned long gb_trace_hits;
#define GB_TRACE_HIT(site) do { ++gb_trace_hits; GB_TRACE_EFFECT_EVENT(site); } while (0)
static void __attribute__((destructor)) gb_trace_dump(void) {
  fprintf(stderr,"TRACE-HITS %lu\\n",gb_trace_hits);
}
''' + coalesced
            if args.bounded_primitive_entries:
                if not any(row['sites'] for row in details['boundedPrimitiveEntrySites']):
                    raise RuntimeError('bounded primitive contract has no actual static coverage')
                coalesced = '''#include <stdio.h>
static unsigned long gb_bounded_hits[3],gb_bounded_reverse_pairs;
#define GB_BOUNDED_PRIMITIVE_HIT(kind,size) do { ++gb_bounded_hits[kind]; if ((kind)==1) gb_bounded_reverse_pairs+=(size); } while (0)
static void __attribute__((destructor)) gb_bounded_dump(void) {
  fprintf(stderr,"BOUNDED-PRIMITIVE-HITS %lu %lu %lu %lu\\n",
    gb_bounded_hits[0],gb_bounded_hits[1],gb_bounded_hits[2],gb_bounded_reverse_pairs);
}
''' + coalesced
            if args.local_subroutine_clones:
                coalesced = '''#include <stdio.h>
static unsigned long gb_micro_hits;
#define GB_MICRO_EVENT() (++gb_micro_hits)
static void __attribute__((destructor)) gb_micro_dump(void) {
  fprintf(stderr,"MICRO-CLONE-HITS %lu\\n",gb_micro_hits);
}
''' + coalesced
                if not sum(row["callsiteCopies"] for row in details["localSubroutineClones"].values()):
                    raise RuntimeError("local subroutine contract must contain actual copies")
                if args.defer_local_frames and not sum(row["deferredFrames"] for row in details["localSubroutineClones"].values()):
                    raise RuntimeError("deferred frame contract must contain actual frame specializations")
            if args.known_return_guards:
                coalesced = '''#include <stdio.h>
static unsigned long gb_known_return_hits;
#define GB_KNOWN_RETURN_EVENT() (++gb_known_return_hits)
static void __attribute__((destructor)) gb_known_return_dump(void) {
  fprintf(stderr,"KNOWN-RETURN-HITS %lu\\n",gb_known_return_hits);
}
''' + coalesced
            if args.vector_entry_guards:
                coalesced = '''#include <stdio.h>
static unsigned long gb_vector_hits, gb_vector_misses;
#define GB_VECTOR_EVENT(kind) ((kind) ? ++gb_vector_hits : ++gb_vector_misses)
static void __attribute__((destructor)) gb_vector_dump(void) {
  fprintf(stderr,"VECTOR-GUARD-COUNTS %lu %lu\\n",gb_vector_hits,gb_vector_misses);
}
''' + coalesced
            if args.guarded_leaf_clones:
                coalesced = '''#include <stdio.h>
static unsigned long gb_leaf_hits;
#define GB_LEAF_EVENT() (++gb_leaf_hits)
static void __attribute__((destructor)) gb_leaf_dump(void) {
  fprintf(stderr,"LEAF-CLONE-HITS %lu\\n",gb_leaf_hits);
}
''' + coalesced
            link.write_text(coalesced)
            report.update(details)
            if args.guarded_trace_lookup_return_branches:
                report['typeChainGeneratorSha256'] = hashlib.sha256(
                    Path(__file__).with_name('gambit_type_chain.py').read_bytes()).hexdigest()
            if args.local_return_guards and not sum(row["returnSites"] for row in details["localReturnGuards"].values()):
                raise RuntimeError("local return contract must exercise rewritten sites")
            if args.gen_entry_count and not details["genericEntryCountCallsites"]:
                raise RuntimeError("generic entry contract must exercise counted sites")
            if args.vector_entry_guards and not sum(row["sites"] for row in details["vectorEntryGuards"].values()):
                raise RuntimeError("vector entry contract must exercise rewritten sites")
            if args.guarded_leaf_clones and not details["guardedLeafClones"]:
                raise RuntimeError("leaf clone contract must contain actual copied sites")
            if args.internal_leaf_clones and not any(row["dispatchKind"] == "internal" for row in details["guardedLeafClones"]):
                raise RuntimeError("internal leaf contract must contain actual copied sites")
            if args.known_return_guards and not sum(row["returnSites"] for row in details["knownReturnGuards"].values()):
                raise RuntimeError("known returns must contain actual rewritten sites")
            if args.known_return_guards and not sum(row["microReturnSites"] for row in details["knownReturnGuards"].values()):
                raise RuntimeError("known returns must cover a local read-only subroutine")
            report["scope"] = "tiny-native-original-host-coalescing-contract"
        compile_c("compile-embedded-link", link)
        binary = output / "embedded-contract"
        run("native-link", [env["CC"], "-o", str(binary), *map(str, objects), str(link.with_suffix(".o")),
                            f"-L{home / 'lib'}", "-lgambit", "-ldl", "-lm"])
        candidate_env = dict(env)
        if args.gen_entry_count:
            trace = output / "gen-trace"
            trace.mkdir()
            candidate_env["GAMBIT_STRUCTURE_PRIMITIVE_DIR"] = str(trace)
        def check_candidate(index):
            name = f"native-contract-{index}"
            run(name, [str(binary)], candidate_env)
            actual = (output / f"{name}.log").read_text()
            if args.bounded_primitive_entries:
                hits = re.findall(r'^BOUNDED-PRIMITIVE-HITS (\d+) (\d+) (\d+) (\d+)$', actual, re.MULTILINE)
                if len(hits) != 1 or any(int(value)<100 for value in hits[0][:3]):
                    raise RuntimeError('bounded primitives must execute 100 actual hits in every category')
                actual = re.sub(r'^BOUNDED-PRIMITIVE-HITS .*\n', '', actual, flags=re.MULTILINE)
            if args.parameter_entry_fastpath:
                hits = re.findall(r"^PARAMETER-HITS (\d+)$", actual, re.MULTILINE)
                if len(hits) != 1 or int(hits[0]) < 100:
                    raise RuntimeError("parameter entry must exercise at least 100 actual hits")
                actual = re.sub(r"^PARAMETER-HITS \d+\n", "", actual, flags=re.MULTILINE)
                slots = re.findall(r"^PARAMETER-SLOTS (\d+) (\d+) (\d+)$", actual, re.MULTILINE)
                if len(slots) != 1 or any(int(value) == 0 for value in slots[0]):
                    raise RuntimeError("parameter entry must hit all three actual slots")
                actual = re.sub(r"^PARAMETER-SLOTS .*\n", "", actual, flags=re.MULTILINE)
                if args.parameter_identity_return:
                    hits = re.findall(r'^PARAMETER-IDENTITY-HITS (\d+)$', actual, re.MULTILINE)
                    if len(hits) != 1 or int(hits[0]) < 100:
                        raise RuntimeError('identity contract requires 100 actual short-circuit hits')
                    actual = re.sub(r'^PARAMETER-IDENTITY-HITS \d+\n', '', actual, flags=re.MULTILINE)
                if args.parameter_env_lookup:
                    hits = re.findall(r'^PARAMETER-ENV-HITS (\d+) (\d+)$', actual, re.MULTILINE)
                    if len(hits) != 1 or any(int(value) == 0 for value in hits[0]):
                        raise RuntimeError('environment contract requires actual default and tree hits')
                    actual = re.sub(r'^PARAMETER-ENV-HITS .*\n', '', actual, flags=re.MULTILINE)
            if args.guarded_readonly_traces:
                if args.guarded_trace_epoch_cache:
                    cached = re.findall(r"^TRACE-CACHE-HITS (\d+)$", actual, re.MULTILINE)
                    if len(cached) != 1 or int(cached[0]) < 100:
                        raise RuntimeError("epoch contract must execute at least 100 real cache hits")
                    actual = re.sub(r"^TRACE-CACHE-HITS \d+\n", "", actual, flags=re.MULTILINE)
                if args.guarded_trace_primitive_boundary:
                    effects = re.findall(r"^TRACE-EFFECT-HITS (\d+)$", actual, re.MULTILINE)
                    if len(effects) != 1 or int(effects[0]) < 100:
                        raise RuntimeError("primitive handoff must execute at least 100 real effects")
                    actual = re.sub(r"^TRACE-EFFECT-HITS \d+\n", "", actual, flags=re.MULTILINE)
                if args.guarded_trace_lookup_return_branches:
                    reentries = re.findall(r'^TRACE-REENTRY-HITS (\d+)$', actual, re.MULTILINE)
                    if len(reentries) != 1 or int(reentries[0]) < 100:
                        raise RuntimeError('lookup loop must execute at least 100 native reentries')
                    actual = re.sub(r'^TRACE-REENTRY-HITS \d+\n', '', actual, flags=re.MULTILINE)
                if args.guarded_trace_polls:
                    counts = re.findall(r"^TRACE-POLL-COUNTS (\d+) (\d+) (\d+)$", actual, re.MULTILINE)
                    if len(counts) != 1 or any(int(value) == 0 for value in counts[0]):
                        raise RuntimeError("poll contract must enter original handler and collect live roots")
                    actual = re.sub(r"^TRACE-POLL-COUNTS .*\n", "", actual, flags=re.MULTILINE)
                hits = re.findall(r"^TRACE-HITS (\d+)$", actual, re.MULTILINE)
                if len(hits) != 1 or int(hits[0]) < 100:
                    raise RuntimeError("readonly trace contract must execute actual success paths")
                actual = re.sub(r"^TRACE-HITS \d+\n", "", actual, flags=re.MULTILINE)
            if args.local_subroutine_clones:
                hits = re.findall(r"^MICRO-CLONE-HITS (\d+)$", actual, re.MULTILINE)
                if len(hits) != 1 or int(hits[0]) < 2:
                    raise RuntimeError("local subroutine contract must execute true and false paths")
                actual = re.sub(r"^MICRO-CLONE-HITS \d+\n", "", actual, flags=re.MULTILINE)
            if args.known_return_guards:
                hits = re.findall(r"^KNOWN-RETURN-HITS (\d+)$", actual, re.MULTILINE)
                if len(hits) != 1 or int(hits[0]) < 4:
                    raise RuntimeError("known returns must execute actual guarded destinations")
                actual = re.sub(r"^KNOWN-RETURN-HITS \d+\n", "", actual, flags=re.MULTILINE)
            if args.guarded_leaf_clones:
                hits = re.findall(r"^LEAF-CLONE-HITS (\d+)$", actual, re.MULTILINE)
                if len(hits) != 1 or int(hits[0]) < 4:
                    raise RuntimeError("leaf contract must execute actual cloned entries")
                actual = re.sub(r"^LEAF-CLONE-HITS \d+\n", "", actual, flags=re.MULTILINE)
            if args.vector_entry_guards:
                counts = re.findall(r"^VECTOR-GUARD-COUNTS (\d+) (\d+)$", actual, re.MULTILINE)
                if len(counts) != 1 or int(counts[0][0]) < 1 or int(counts[0][1]) < 2:
                    raise RuntimeError("vector contract must execute guarded and fallback branches")
                actual = re.sub(r"^VECTOR-GUARD-COUNTS \d+ \d+\n", "", actual, flags=re.MULTILINE)
            if args.gen_entry_count:
                if not re.search(r"^GEN-LABEL-ALIASES \d+$", actual, re.MULTILINE):
                    raise RuntimeError("generic entry diagnostic must dump actual counters")
                actual = re.sub(r"^GEN-LABEL-ALIASES \d+\n", "", actual, flags=re.MULTILINE)
            if actual != expected:
                raise RuntimeError("initialization, alias, rebinding, GC or result contract failed")
        with ThreadPoolExecutor(max_workers=cores) as pool:
            list(pool.map(check_candidate, range(cores)))
        if args.gen_entry_count:
            counted = {"internal": 0, "external": 0, "nonProcedure": 0}
            files = sorted(trace.glob("*-gen.tsv"))
            if len(files) != cores:
                raise RuntimeError("all native counter processes must dump evidence")
            for path in files:
                with path.open() as stream:
                    for row in csv.DictReader(stream, delimiter="\t"):
                        target = int(row["target"])
                        key = "external" if target == 65534 else "nonProcedure" if target == 65535 else "internal"
                        counted[key] += int(row["calls"])
            if not all(counted.values()):
                raise RuntimeError("generic diagnostic must count local, external and nonprocedure paths")
            report["genericEntryObservedCalls"] = counted
        report.update(qualified=True, originalObjectNames=[path.name for path in objects],
                      moduleAliasesVerified=True, initializationOrderVerified=True,
                      legacyResourceDefinitionsRetained=True, crossModuleRebindingVerified=True,
                      nonProcedureExceptionVerified=True, explicitGcPerProcess=200,
                      continuationWindAndValuesVerified=True, schemeThreadsPerProcess=12,
                      restArityRangeVerified=[0, 12], restFreshnessAndOrderVerified=True,
                      concurrentCandidateProcesses=cores)
    except BaseException as error:
        report["failure"] = repr(error)
        raise
    finally:
        (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
