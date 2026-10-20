#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../../.." && pwd)
home=${1:?matching runtime home required}
driver=${2:?owned native producer-proof driver bin required}
output=${3:?fresh owned output required}
case "$home:$driver:$output" in "$root"/.data/*:"$root"/.data/*:"$root"/.data/*) ;; *) exit 2 ;; esac
test ! -e "$output"
test -f "$driver/gerbil" && test ! -L "$driver/gerbil"
mkdir -p "$output"
trap 'status=$?; printf "%s\n" "$status" > "$output/exit-status.txt"' EXIT
cp "$root/patches/gerbil-v19-darwin/tests/producer_handoff_entry.ss" "$output/entry.ss"
export GERBIL_HOME="$home" GERBIL_LOADPATH="$home/lib" GERBIL_GSC="$driver/gsc"
export GERBIL_PATH="$output/prefix"
export GERBIL_GCC=/opt/homebrew/bin/gcc-16
export GAMBOPT="~~bin=$driver,~~lib=$home/lib,~~include=$home/include"
export PATH="/opt/homebrew/bin:/usr/bin:/bin:$PATH"
export GAMBIT_DARWIN_CLOSED_LINK_REUSE=1 GAMBIT_GENERATED_C_IN_PROCESS_DIGESTS=1
export GAMBIT_DARWIN_CLOSED_LINK_PRODUCER_PROOF=1 GAMBIT_DARWIN_BOUND_SINGLE_PASS=1
unset GAMBIT_DARWIN_BOUND_COLD_CAPTURE GAMBIT_DARWIN_STATIC_EXPECTED_SOURCE_SHA
unset GAMBIT_DARWIN_NATIVE_GENERATED_C GAMBIT_GENERATED_C_PRODUCER_INDEX
unset GAMBIT_GENERATED_C_BATCH_DIGESTS
unset CC CFLAGS CPPFLAGS LDFLAGS CPATH C_INCLUDE_PATH CPLUS_INCLUDE_PATH
unset NIX_CFLAGS_COMPILE NIX_LDFLAGS DEVELOPER_DIR SDKROOT
export LIBRARY_PATH="$(brew --prefix openssl@3)/lib"
expression="(import :gerbil/compiler :gerbil/compiler/base)
 (def opts [output-dir: \"$output/lib\" output-file: \"$output/entry\"
            parallel: #t verbose: #t invoke-gsc: #t static: #t])
 (compile-module \"$output/entry.ss\" opts)
 (add-compile-dependent-job! [\"$output/lib/entry~0.c\"]
   (lambda ()
     (copy-file \"$output/lib/static/entry.o\" \"$output/producer.o\")
     (copy-file \"$output/lib/static/entry.o.gambit-static-proof\" \"$output/producer.proof\")
     (displayln \"PRODUCER-PROOF-READY\")
     (compile-exe \"$output/entry.ss\" opts)))
 (execute-pending-compile-jobs!)"
/usr/bin/time -p -o "$output/time.txt" "$driver/gxi" -e "$expression" > "$output/build.log" 2>&1
rg -q '^PRODUCER-PROOF-READY$' "$output/build.log"
rg -q '^GAMBIT-STATIC-BOUND-SINGLE-PASS$' "$output/build.log"
# Parallel verbose output can split either side of the backend's stderr marker.
# Exact object and proof comparisons below are the substantive handoff checks.
rg -q 'GAMBIT-STATIC-OBJECT-HIT' "$output/build.log"
rg -q -- '-closed-c-binding' "$output/build.log"
cmp "$output/producer.o" "$output/lib/static/entry.o"
cmp "$output/producer.proof" "$output/lib/static/entry.o.gambit-static-proof"
"$output/entry" > "$output/native.stdout"
test "$(cat "$output/native.stdout")" = PRODUCER-HANDOFF-NATIVE-OK
printf 'PRODUCER-HANDOFF-OK actual-producer full-proof-hit object-parity native-execution\n'
