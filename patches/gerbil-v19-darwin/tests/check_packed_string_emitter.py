#!/usr/bin/env python3
"""Execute the actual emitter and compare native objects with portable STR output."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

from bazel_host_environment import build_environment


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--syntax-only", action="store_true")
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[3]
    output = args.output.resolve()
    source = args.source.resolve()
    baseline = args.baseline.resolve()
    if not all(p.is_relative_to(repo / ".data") for p in (output, source, baseline)):
        parser.error("all inputs and evidence must remain in project .data")
    output.mkdir(exist_ok=False)
    env = build_environment()
    full_context = '(##namespace ("c#"))(##include "../lib/header.scm")(##include "_t-c-1.scm")'
    syntax = '(begin (##compile-top ##interaction-cte (vector-ref ' + \
        '(##read-all-as-a-begin-expr-from-string ' + json.dumps(full_context) + \
        ') 1)) (display "FULL-EMITTER-CONTEXT-SYNTAX-OK") (newline))'
    result = subprocess.run([str(baseline / "build/bin/gsc"),
                            "-:~~lib=" + str(source / "src/gambit/lib"), "-e", syntax],
                            cwd=source / "src/gambit/gsc", env=env,
                            capture_output=True, text=True, timeout=120)
    (output / "full-source-syntax.log").write_text(result.stdout + result.stderr)
    if result.returncode or "FULL-EMITTER-CONTEXT-SYNTAX-OK" not in result.stdout:
        raise RuntimeError("actual full-file Gambit macro expansion failed")
    print("FULL-EMITTER-CONTEXT-SYNTAX-OK", flush=True)
    if args.syntax_only:
        return
    context = '(##namespace ("c#"))(##include "../lib/header.scm")(include "fixnum.scm")'
    # Even/odd tails, chunk boundaries, threshold, and supplementary Unicode.
    lengths = [0, 1, 7, 8, 9, 4095, *range(4096, 4105)]
    report = {"qualified": False, "performanceQualified": False, "objects": []}
    for packed in (False, True):
        path = output / ("packed.c" if packed else "portable.c")
        expression = context + f'''
(set! c#targ-darwin-packed-strings? {'#t' if packed else '#f'})
(set! c#targ-port (open-output-file {json.dumps(str(path))}))
(set! c#targ-source-filename #f)
(set! c#targ-line-size 0)
(set! c#targ-line-number 0)
(set! c#targ-current-line-number 0)
(c#targ-display "#include <gambit.h>") (c#targ-line)
(let loop ((lengths '{lengths!s}) (index 0))
  (if (pair? lengths)
      (let* ((n (car lengths)) (s (make-string n)))
        (let fill ((i 0))
          (if (< i n)
              (begin
                (string-set! s i (integer->char
                  (list-ref '(0 65 255 256 65535 65536 1114111) (modulo i 7))))
                (fill (+ i 1)))))
        (c#targ-dump-string s (string-append "fixture_" (number->string index)))
        (loop (cdr lengths) (+ index 1)))))
(c#targ-display "unsigned long long fixture_checksum(void) {{ unsigned long long x=0;")
(c#targ-line)
(let loop ((index 0))
  (if (< index {len(lengths)})
      (begin
        (c#targ-display (string-append
          "for(unsigned long i=0;i<sizeof(fixture_" (number->string index)
          ")/sizeof(___WORD);i++) x=x*33+fixture_" (number->string index) "[i];"))
        (c#targ-line) (loop (+ index 1)))))
(c#targ-display "return x; }}") (c#targ-line)
(close-output-port c#targ-port)
(display "EMITTER-EXECUTION-OK") (newline)
'''.replace(str(lengths), "(" + " ".join(map(str, lengths)) + ")")
        # Read the changed definitions from the actual source, without replacing
        # every live native compiler global with an interpreted implementation.
        loader = '''
(define emitter-forms
  (call-with-input-file "_t-c-1.scm"
    (lambda (port)
      (let loop ((forms '()))
        (let ((form (read port)))
          (if (eof-object? form)
              (reverse forms)
              (loop
                (if (and (pair? form) (eq? (car form) 'define)
                         (memq (if (pair? (cadr form))
                                   (caadr form) (cadr form))
                               '(c#targ-darwin-packed-strings? targ-dump-string)))
                    (cons form forms) forms))))))))
(if (not (= (length emitter-forms) 2)) (error "missing actual emitter forms"))
(display "EMITTER-FORMS-READ\n") (force-output)
'''
        expression = loader + "(##setup-requirements-and-run (##compile-top ##interaction-cte (vector-ref (##read-all-as-a-begin-expr-from-string (string-append " + json.dumps(context) + \
            " (with-output-to-string (lambda () (for-each write emitter-forms))) " + \
            json.dumps(expression[len(context):]) + ")) 1)) #f)"
        expression = '(begin (display "READING-EMITTER\\n") (force-output) ' + expression + ")"
        (output / f"{path.stem}-driver.scm").write_text(expression + "\n")
        result = subprocess.run([str(baseline / "build/bin/gsc"),
                                "-:~~lib=" + str(source / "src/gambit/lib"), "-e", expression],
                                cwd=source / "src/gambit/gsc", env=env,
                                capture_output=True, text=True, timeout=120)
        (output / f"{path.stem}-emit.log").write_text(
            f"exitCode={result.returncode}\n" + result.stdout + result.stderr)
        if result.returncode or "EMITTER-EXECUTION-OK" not in result.stdout:
            raise RuntimeError(f"{path.stem} emitter failed; inspect durable log")
        text = path.read_text()
        if ("0x" in text) != packed:
            raise RuntimeError("packed branch did not execute as requested")
        obj = path.with_suffix(".o")
        command = [env["CC"], "-O1", "-fPIC", "-fwrapv", "-fno-strict-aliasing",
                   "-ftrack-macro-expansion=0", "-I" + str(baseline / "build/include"),
                   "-c", str(path), "-o", str(obj)]
        result = subprocess.run(command, env=env, capture_output=True, text=True, timeout=120)
        (output / f"{path.stem}-compile.log").write_text(result.stdout + result.stderr)
        if result.returncode:
            raise RuntimeError(f"{path.stem} GNU compilation failed")
        report["objects"].append({"variant": path.stem,
                                  "sha256": hashlib.sha256(obj.read_bytes()).hexdigest()})
        print(f"OK actual-emitter/GNU-object {path.stem}", flush=True)
    report["qualified"] = len({r["sha256"] for r in report["objects"]}) == 1
    report["lengths"] = lengths
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    if not report["qualified"]:
        raise RuntimeError("native objects differ")
    print("PACKED-EMITTER-OBJECT-EQUIVALENCE-OK", flush=True)


if __name__ == "__main__":
    main()
