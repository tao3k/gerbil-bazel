#!/usr/bin/env python3
"""Native std/test contracts for an isolated cons tail-marking candidate."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
import os
import re
from pathlib import Path
import shlex
import subprocess

from bazel_host_environment import build_environment


EXPRESSION = r'''
(import :std/test :std/test/base)
(def (graph-check seed rounds)
  (let* ((shared (cons seed (list (+ seed 1))))
         (spine (let loop ((n 2000) (r []))
                  (if (zero? n) r (loop (- n 1) (cons shared r)))))
         (cycle (cons shared #f))
         (car-cycle (cons #f shared))
         (keep (lambda () (vector shared spine cycle car-cycle)))
         (keys (let loop ((n 1024) (r []))
                 (if (zero? n) r (loop (- n 1) (cons (cons n shared) r)))))
         (table (make-hash-table-eq)))
    (set-cdr! cycle cycle)
    (set-car! car-cycle car-cycle)
    (hash-put! table shared spine)
    (for-each (lambda (key) (hash-put! table key shared)) keys)
    (let loop ((rest keys) (index 0))
      (unless (null? rest)
        (when (zero? (modulo index 3)) (hash-remove! table (car rest)))
        (loop (cdr rest) (+ index 1))))
    (let loop ((n rounds))
      (unless (zero? n)
        (##gc)
        (check-eq? (car spine) shared)
        (check-eq? (car (list-tail spine 1999)) shared)
        (check (length spine) => 2000)
        (check-eq? (cdr cycle) cycle)
        (check-eq? (car car-cycle) car-cycle)
        (check-eq? (cdr car-cycle) shared)
        (check-eq? (vector-ref (keep) 0) shared)
        (check-eq? (vector-ref (keep) 1) spine)
        (check-eq? (hash-get table shared) spine)
        (let loop ((rest keys) (index 0))
          (unless (null? rest)
            (if (zero? (modulo index 3))
              (check (hash-get table (car rest)) => #f)
              (check-eq? (hash-get table (car rest)) shared))
            (loop (cdr rest) (+ index 1))))
        (check (car shared) => seed)
        (set-car! shared (+ seed 1))
        (##gc)
        (check (car (car spine)) => (+ seed 1))
        (set-car! shared seed)
        (loop (- n 1))))
    (let (answer (call/cc (lambda (return) (##gc) (return (keep)))))
      (check-eq? (vector-ref answer 2) cycle))))
(def suite
  (test-suite "GC pair tail"
    (test-case "sharing cycles mutation closures continuations and hash keys"
      (graph-check 11 12))
    (test-case "twelve Scheme threads"
      (let (threads
            (map (lambda (n)
                   (make-thread (lambda () (thread-yield!) (graph-check n 2))))
                 '(1 2 3 4 5 6 7 8 9 10 11 12)))
        (for-each thread-start! threads)
        (for-each thread-join! threads)))))
(def harness (TestHarness "GC pair tail" (TestConfig verbosity: VERBOSITY-CASE capture-output?: #f)
                         (list (TestModule "native" (list suite) [] void void))))
(def result (test-run! harness))
(when (test-result-error? result) (error "GC pair tail native test failed" result))
(displayln "GC-PAIR-TAIL-OK")
(force-output)
'''


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--expected-branch", default="GAMBIT_DARWIN_PAIR_TAIL_CDR")
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[3]
    baseline, candidate, output = (path.resolve() for path in (args.baseline, args.candidate, args.output))
    if not all(path.is_relative_to(repo / ".data") for path in (baseline, candidate, output)):
        parser.error("isolated sources and receipts under project .data required")
    output.mkdir(parents=True, exist_ok=False)
    env = build_environment()
    home = baseline / "build"
    env.update(GERBIL_HOME=str(home), GERBIL_LOADPATH=str(home / "lib"),
               GAMBOPT=f"~~bin={home / 'bin'},~~lib={home / 'lib'},~~include={home / 'include'}")
    lib = candidate / "src/gambit/lib"
    dry = subprocess.check_output(["make", "-n", "-B", "mem.o"], cwd=lib, env=env, text=True)
    commands = [shlex.split(line) for line in dry.splitlines() if line.startswith(env["CC"] + " ")]
    if len(commands) != 1:
        raise RuntimeError("ambiguous official mem.o command")
    command = []
    skip = False
    for argument in commands[0]:
        if skip:
            skip = False
        elif argument == "-o":
            skip = True
        elif argument != "-c":
            command.append(argument)
    macros = subprocess.check_output([*command, "-E", "-dM"], cwd=lib, env=env, text=True)
    if not re.fullmatch(r"[A-Z][A-Z0-9_]+", args.expected_branch):
        parser.error("a C macro name is required")
    if f"#define {args.expected_branch} 1\n" not in macros:
        raise RuntimeError("the candidate GC branch is not compiled")
    report = {"qualified": False, "performanceQualified": False, "cores": os.cpu_count(),
              "scope": "native-std-test-gc-contract-not-startup-performance",
              "candidateBranchActive": True, "runs": [],
              "candidateBranch": args.expected_branch,
              "expressionSha256": hashlib.sha256(EXPRESSION.encode()).hexdigest()}
    (output / "expression.txt").write_text(EXPRESSION)

    def run(label, binary):
        local = dict(env, GERBIL_PATH=str(output / f"empty-{label}"))
        with (output / f"{label}.log").open("w") as log:
            process = subprocess.Popen([str(binary), "-e", EXPRESSION], env=local,
                                       stdout=log, stderr=subprocess.STDOUT)
            try:
                status = process.wait(timeout=180)
            finally:
                if process.poll() is None:
                    process.kill()
                    process.wait()
        text = (output / f"{label}.log").read_text()
        if status or not text.rstrip().endswith("GC-PAIR-TAIL-OK") or "HARNESS-OK" not in text:
            raise RuntimeError(f"{label} failed; see retained native log")
        print(f"GC-PAIR-TAIL-OK {label}", flush=True)
        return {"label": label, "exitCode": status, "harnessPassed": True}

    try:
        report["runs"].append(run("original", home / "bin/gxi"))
        with ThreadPoolExecutor(max_workers=os.cpu_count()) as pool:
            pending = [pool.submit(run, f"candidate-{index}", candidate / "build/bin/gxi")
                       for index in range(os.cpu_count())]
            for future in as_completed(pending):
                report["runs"].append(future.result())
        report["qualified"] = True
    except BaseException as error:
        report["failure"] = repr(error)
        raise
    finally:
        (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
