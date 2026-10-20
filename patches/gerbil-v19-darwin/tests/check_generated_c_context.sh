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
/usr/bin/shasum -a 256 "$bin/gsc" > compiler.sha256
printf '(define dependency-value 17)\n' > value.scm
printf '(include "value.scm")\n(define (answer) dependency-value)\n' > direct.scm
/usr/bin/shasum -a 256 direct.scm > direct-before.sha256
"$bin/gsc" -link -flat direct.scm > direct-first.log 2>&1
cp direct.c direct-reference.c
"$bin/gsc" -link -flat direct.scm > direct-repeat.log 2>&1
cmp direct-reference.c direct.c
printf 'GENERATED-C-CONTEXT-OK unchanged\n'
printf '(define dependency-value 29)\n' > value.scm
"$bin/gsc" -link -flat direct.scm > direct-changed.log 2>&1
if cmp -s direct-reference.c direct.c; then exit 1; fi
/usr/bin/shasum -a 256 direct.scm > direct-after.sha256
cmp direct-before.sha256 direct-after.sha256
printf 'GENERATED-C-CONTEXT-OK include-change\n'

printf '(define (answer) (context-value))\n' > prelude.scm
/usr/bin/shasum -a 256 prelude.scm > prelude-before.sha256
"$bin/gsc" -link -flat -prelude '(define-macro (context-value) 17)' \
  prelude.scm > prelude-first.log 2>&1
cp prelude.c prelude-reference.c
"$bin/gsc" -link -flat -prelude '(define-macro (context-value) 29)' \
  prelude.scm > prelude-changed.log 2>&1
if cmp -s prelude-reference.c prelude.c; then exit 1; fi
/usr/bin/shasum -a 256 prelude.scm > prelude-after.sha256
cmp prelude-before.sha256 prelude-after.sha256
printf 'GENERATED-C-CONTEXT-OK prelude-change\n'

# The source reader alone cannot discover an include emitted by a macro.
printf '(define-macro (dependency) (list (quote include) "value.scm"))\n(dependency)\n(define (answer) dependency-value)\n' > macro.scm
/usr/bin/shasum -a 256 macro.scm > macro-before.sha256
"$bin/gsc" -link -flat macro.scm > macro-first.log 2>&1
cp macro.c macro-reference.c
printf '(define dependency-value 41)\n' > value.scm
"$bin/gsc" -link -flat macro.scm > macro-changed.log 2>&1
if cmp -s macro-reference.c macro.c; then exit 1; fi
/usr/bin/shasum -a 256 macro.scm > macro-after.sha256
cmp macro-before.sha256 macro-after.sha256
printf 'GENERATED-C-CONTEXT-OK macro-emitted-include\n'

printf '(include "value.scm")\n(define (answer) dependency-value)\n' > failure.scm
"$bin/gsc" -link -flat failure.scm > failure-reference.log 2>&1
cp failure.c failure-before.c
printf '(define dependency-value\n' > value.scm
if "$bin/gsc" -link -flat failure.scm > failure.log 2>&1; then exit 1; fi
if test -f failure.c && cmp -s failure-before.c failure.c; then
  printf 'GENERATION-FAILURE-LEAVES-OLD-C\n'
else
  printf 'GENERATION-FAILURE-REMOVES-OR-CHANGES-C\n'
fi
printf 'GENERATED-C-CONTEXT-OK failed-dependency\n'
printf 'GENERATED-C-CONTEXT-CONTRACT-OK 5\n'
