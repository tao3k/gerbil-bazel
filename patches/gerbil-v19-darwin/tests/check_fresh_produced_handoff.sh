#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../../.." && pwd)
home=${1:?matching runtime home required}
bin=${2:?owned fresh-produced AOT bin required}
output=${3:?fresh owned receipt required}
mode=${4:-success}
case "$home:$bin:$output" in "$root"/.data/*:"$root"/.data/*:"$root"/.data/*) ;; *) exit 2 ;; esac
case "$mode" in success|mismatch) ;; *) exit 2 ;; esac
test ! -e "$output"
mkdir -p "$output"
trap 'status=$?; printf "%s\n" "$status" > "$output/exit-status.txt"' EXIT
cp "$root/patches/gerbil-v19-darwin/tests/producer_handoff_entry.ss" "$output/entry.ss"
export GERBIL_HOME="$home" GERBIL_PATH="$output/prefix" GERBIL_LOADPATH="$home/lib"
export GERBIL_GSC="$bin/gsc" GERBIL_GCC=/opt/homebrew/bin/gcc-16
export GAMBOPT="~~bin=$bin,~~lib=$home/lib,~~include=$home/include"
export PATH="/opt/homebrew/bin:/usr/bin:/bin:$PATH"
export GAMBIT_DARWIN_CLOSED_LINK_REUSE=1 GAMBIT_GENERATED_C_IN_PROCESS_DIGESTS=1
export GAMBIT_DARWIN_CLOSED_LINK_FRESH_OBJECTS=1
export GAMBIT_DARWIN_NATIVE_OBJECT_CAPTURE=1 GAMBIT_DARWIN_NATIVE_OBJECT_CHECK=1 GAMBIT_DARWIN_BOUND_SINGLE_PASS=1
unset GAMBIT_DARWIN_CLOSED_LINK_PRODUCER_PROOF GAMBIT_DARWIN_BOUND_COLD_CAPTURE
unset GAMBIT_DARWIN_STATIC_EXPECTED_SOURCE_SHA GAMBIT_DARWIN_NATIVE_GENERATED_C
unset GAMBIT_GENERATED_C_PRODUCER_INDEX GAMBIT_GENERATED_C_BATCH_DIGESTS
unset CC CFLAGS CPPFLAGS LDFLAGS CPATH C_INCLUDE_PATH CPLUS_INCLUDE_PATH
unset NIX_CFLAGS_COMPILE NIX_LDFLAGS DEVELOPER_DIR SDKROOT
export LIBRARY_PATH="$(brew --prefix openssl@3)/lib"
mutation=''
if test "$mode" = mismatch; then
  mutation="(call-with-output-file \"$output/lib/static/entry.c\"
               (lambda (port) (display \"void changed_definition(void) {}\" port)))"
fi
expression="(import :gerbil/compiler :gerbil/compiler/base)
 (def opts [output-dir: \"$output/lib\" output-file: \"$output/entry\"
            parallel: #t verbose: #t invoke-gsc: #t static: #t])
 (compile-module \"$output/entry.ss\" opts)
 (add-compile-dependent-job! [\"$output/lib/entry~0.c\"]
   (lambda ()
     (copy-file \"$output/lib/static/entry.o\" \"$output/producer.o\")
     $mutation
     (compile-exe \"$output/entry.ss\" opts)))
 (execute-pending-compile-jobs!)"
status=0
/usr/bin/time -p -o "$output/time.txt" "$bin/gxi" -e "$expression" > "$output/build.log" 2>&1 || status=$?
cmp "$output/producer.o" "$output/lib/static/entry.o"
test ! -e "$output/lib/static/entry.o.gambit-static-proof"
test "$(rg -c -- ' -obj .*[/]entry[.]c[)]' "$output/build.log")" = 1
if test "$mode" = mismatch; then
  test "$status" != 0
  rg -q 'Fresh producer C differs from link binding' "$output/build.log"
  test ! -e "$output/entry"
  printf 'FRESH-PRODUCED-MISMATCH-OK source-binding-rejected old-object-preserved no-executable\n'
else
  test "$status" = 0
  "$output/entry" > "$output/native.stdout"
  test "$(cat "$output/native.stdout")" = PRODUCER-HANDOFF-NATIVE-OK
  printf 'FRESH-PRODUCED-HANDOFF-OK original-production single-object-compile exact-object-parity native-execution\n'
fi
