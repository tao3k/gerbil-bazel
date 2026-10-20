#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../../.." && pwd)
bin=${1:?isolated compiler bin required}
output=${2:?fresh output required}
case "$bin:$output" in "$root"/.data/*:"$root"/.data/*) ;; *) exit 2 ;; esac
test ! -e "$output"
mkdir -p "$output"
home=$(cd "$bin/.." && pwd)
export GERBIL_HOME="$home"
export GAMBOPT="~~bin=$bin,~~lib=$home/lib,~~include=$home/include"
export PATH="/opt/homebrew/bin:/usr/bin:/bin:$PATH"
cd "$output"
printf '(define dependency-value 17)\n' > leaf.scm
printf '(include "leaf.scm")\n' > middle.scm
printf '(include "middle.scm")\n(define (answer) dependency-value)\n' > direct.scm
printf '(define-macro (dependency) (list (quote include) "middle.scm"))\n(dependency)\n(define (answer) dependency-value)\n' > macro.scm
for name in direct macro; do
  mkdir "$name-snapshots"
  export READ_PROBE_ROOT="$output" READ_PROBE_NAME="$name"
  export READ_PROBE_IMPLEMENTATION="$root/patches/gerbil-v19-darwin/tests/gambit-generated-c-reads.scm"
  "$bin/gsc" -e '(load (getenv "READ_PROBE_IMPLEMENTATION"))' \
    -e '(let* ((root (getenv "READ_PROBE_ROOT")) (name (getenv "READ_PROBE_NAME")) (base (string-append root "/" name))) (record-generated-c-reads! (string-append base ".scm") (quote ()) (string-append base ".c") (string-append base "-snapshots") (string-append base ".reads")))' \
    > "$name.log" 2>&1
  "$bin/gsc" -e '(let* ((root (getenv "READ_PROBE_ROOT")) (name (getenv "READ_PROBE_NAME")) (record (call-with-input-file (string-append root "/" name ".reads") read)) (reads (list-ref record 4))) (if (not (equal? (map (lambda (entry) (path-strip-directory (car entry))) reads) (list (string-append name ".scm") "middle.scm" "leaf.scm"))) (error "incomplete dependency journal")) (for-each (lambda (entry) (if (not (equal? (call-with-input-file (car entry) read-all) (call-with-input-file (cadr entry) read-all))) (error "snapshot drift"))) reads) (display "GENERATED-C-READS-OK ") (display name) (newline))' \
    > "$name-verify.log" 2>&1
  cat "$name-verify.log"
  cmp "$name.scm" "$name-snapshots/0.source"
  cmp middle.scm "$name-snapshots/1.source"
  cmp leaf.scm "$name-snapshots/2.source"
done
"$bin/gsc" -e '(load (getenv "READ_PROBE_IMPLEMENTATION"))' \
  -e '(let ((direct (call-with-input-file "direct.reads" read)) (macro (call-with-input-file "macro.reads" read))) (if (or (not (eq? (car direct) (quote generated-c-source-reads-v2))) (not (eq? (car macro) (quote generated-c-source-reads-v2))) (not (equal? (list-ref direct 5) (quote (source-macro-context #f)))) (not (equal? (list-ref macro 5) (quote (source-macro-context #t))))) (error "macro context not identified")) (if (generated-c-source-macro-context? (quote (quote (define-macro (x) 1)))) (error "quoted data is not a compiler macro")) (display "GENERATED-C-READS-OK macro-context-marker\n"))' \
  -e '(exit)' > macro-marker.log 2>&1
cat macro-marker.log
# A generation error must not publish a manifest despite leftover output C.
cp direct.c failure.c
cp direct.scm failure.scm
printf '(define dependency-value\n' > leaf.scm
mkdir failure-snapshots
export READ_PROBE_NAME=failure
if "$bin/gsc" -e '(load (getenv "READ_PROBE_IMPLEMENTATION"))' \
  -e '(let* ((root (getenv "READ_PROBE_ROOT")) (base (string-append root "/failure"))) (record-generated-c-reads! (string-append base ".scm") (quote ()) (string-append base ".c") (string-append base "-snapshots") (string-append base ".reads")))' \
  > failure.log 2>&1; then exit 1; fi
test ! -e failure.reads
printf 'GENERATED-C-READS-OK failure-no-publication\n'
printf 'GENERATED-C-READS-CONTRACT-OK 4\n'
