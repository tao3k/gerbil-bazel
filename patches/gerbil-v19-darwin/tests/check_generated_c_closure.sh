#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../../.." && pwd)
bin=${1:?isolated compiler bin required}
output=${2:?fresh output required}
adapter=${3:-}
case "$bin:$output" in "$root"/.data/*:"$root"/.data/*) ;; *) exit 2 ;; esac
test ! -e "$output"
mkdir -p "$output"
home=$(cd "$bin/.." && pwd)
if test -n "${4:-}"; then
  case "$4" in "$root"/.data/*) ;; *) exit 2 ;; esac
  home=$4
fi
export GERBIL_HOME="$home"
export GAMBOPT="~~bin=$bin,~~lib=$home/lib,~~include=$home/include"
export PATH="/opt/homebrew/bin:/usr/bin:/bin:$PATH"
export GENERATION_FIXTURE="$output" GENERATION_BIN="$bin"
export GENERATION_JOURNAL="$root/patches/gerbil-v19-darwin/tests/gambit-generated-c-reads.scm"
export GENERATION_IMPLEMENTATION="$root/patches/gerbil-v19-darwin/tests/gambit-generated-c-closure.scm"
export GENERATION_CONTRACT="$root/patches/gerbil-v19-darwin/tests/generated_c_closure_contract.scm"
export GENERATION_DIGEST_ADAPTER="$adapter"
if test -n "$adapter"; then
  case "$adapter" in "$root"/patches/gerbil-v19-darwin/tests/*) ;; *) exit 2 ;; esac
  test -f "$adapter" && test ! -L "$adapter"
fi
"$bin/gsc" -e '(load (getenv "GENERATION_JOURNAL"))' \
  -e '(load (getenv "GENERATION_IMPLEMENTATION"))' \
  -e '(if (not (string=? (getenv "GENERATION_DIGEST_ADAPTER") "")) (load (getenv "GENERATION_DIGEST_ADAPTER")))' \
  -e '(load (getenv "GENERATION_CONTRACT"))' \
  -e '(run-generated-c-closure-contract!)' > "$output/output.log" 2>&1
cat "$output/output.log"
rg -q '^GENERATED-C-CLOSURE-CONTRACT-OK 15$' "$output/output.log"
mkdir "$output/concurrent-a" "$output/concurrent-b"
"$bin/gsc" -e '(load (getenv "GENERATION_JOURNAL"))' \
  -e '(load (getenv "GENERATION_IMPLEMENTATION"))' \
  -e '(if (not (string=? (getenv "GENERATION_DIGEST_ADAPTER") "")) (load (getenv "GENERATION_DIGEST_ADAPTER")))' \
  -e '(load (getenv "GENERATION_CONTRACT"))' \
  -e '(run-concurrent-generated-c-closure! "a")' > "$output/concurrent-a.log" 2>&1 &
first=$!
"$bin/gsc" -e '(load (getenv "GENERATION_JOURNAL"))' \
  -e '(load (getenv "GENERATION_IMPLEMENTATION"))' \
  -e '(if (not (string=? (getenv "GENERATION_DIGEST_ADAPTER") "")) (load (getenv "GENERATION_DIGEST_ADAPTER")))' \
  -e '(load (getenv "GENERATION_CONTRACT"))' \
  -e '(run-concurrent-generated-c-closure! "b")' > "$output/concurrent-b.log" 2>&1 &
second=$!
first_status=0
second_status=0
wait "$first" || first_status=$?
wait "$second" || second_status=$?
test "$first_status" = 0 && test "$second_status" = 0
rg -q '^GAMBIT-GENERATED-C-HIT$' "$output/concurrent-a.log" "$output/concurrent-b.log"
cmp "$output/module.c" "$output/published/module.c"
test ! -e "$output/published/closure.proof.lock"
test "$(/usr/bin/stat -f '%Lp' "$output/published/closure.proof")" = 600
! rg -q 'private-context-value|GAMBIT_GENERATION_PRIVACY_FIXTURE' "$output/published/closure.proof"
printf 'GENERATED-C-CLOSURE-CONCURRENCY-OK 2\n'
