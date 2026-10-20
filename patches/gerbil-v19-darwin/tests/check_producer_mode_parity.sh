#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../../.." && pwd)
original=${1:?owned original compiler home required}
candidate=${2:?owned candidate compiler home required}
output=${3:?fresh owned receipt required}
mode=${4:-steady}
case "$mode" in steady|options-change) ;; *) exit 2 ;; esac
pipeline=${5:-fresh}
case "$pipeline" in fresh|recipe) ;; *) exit 2 ;; esac
case "$original:$candidate:$output" in "$root"/.data/*:"$root"/.data/*:"$root"/.data/*) ;; *) exit 2 ;; esac
test ! -e "$output"
mkdir "$output"
trap 'status=$?; printf "%s\n" "$status" > "$output/exit-status.txt"' EXIT
unset CC CFLAGS CPPFLAGS LDFLAGS CPATH C_INCLUDE_PATH CPLUS_INCLUDE_PATH
unset NIX_CFLAGS_COMPILE NIX_LDFLAGS DEVELOPER_DIR SDKROOT
unset GAMBIT_DARWIN_CLOSED_LINK_PRODUCER_PROOF GAMBIT_DARWIN_BOUND_COLD_CAPTURE
unset GAMBIT_DARWIN_STATIC_EXPECTED_SOURCE_SHA GAMBIT_DARWIN_NATIVE_GENERATED_C
unset GAMBIT_GENERATED_C_PRODUCER_INDEX GAMBIT_GENERATED_C_BATCH_DIGESTS
export LIBRARY_PATH="$(brew --prefix openssl@3)/lib"
export GERBIL_GCC=/opt/homebrew/bin/gcc-16
# Match the qualified GNU GCC path; inherited Nix ld is not the Darwin linker.
export PATH="/opt/homebrew/bin:/usr/bin:/bin:$PATH"
test "$(command -v ld)" = /usr/bin/ld
consume_opts=opts
expected=PRODUCER-MODE=17
if test "$mode" = options-change; then
  consume_opts='[gsc-options: ["-cc-options" "-U___DYNAMIC"] opts ...]'
  expected=PRODUCER-MODE=29
fi
for role in original candidate; do
  home=$original
  if test "$role" = candidate; then home=$candidate; fi
  workspace="$output/$role"
  mkdir "$workspace"
  cp "$root/patches/gerbil-v19-darwin/tests/producer_mode_entry.ss" "$workspace/entry.ss"
  export GERBIL_HOME="$home" GERBIL_PATH="$workspace/prefix" GERBIL_LOADPATH="$home/lib"
  export GERBIL_GSC="$candidate/bin/gsc"
  export GAMBOPT="~~bin=$candidate/bin,~~lib=$home/lib,~~include=$home/include"
  unset GAMBIT_DARWIN_CLOSED_LINK_REUSE GAMBIT_GENERATED_C_IN_PROCESS_DIGESTS
  unset GAMBIT_DARWIN_CLOSED_LINK_FRESH_OBJECTS GAMBIT_DARWIN_STATIC_OBJECT_REUSE
  unset GAMBIT_DARWIN_NATIVE_OBJECT_CAPTURE GAMBIT_DARWIN_NATIVE_OBJECT_CHECK GAMBIT_DARWIN_BOUND_SINGLE_PASS
  unset GAMBIT_DARWIN_CLOSED_LINK_RECIPE_PROOF GAMBIT_DARWIN_CLOSED_LINK_PRODUCER_PROOF
  proof_copy=''
  if test "$role" = candidate; then
    export GAMBIT_DARWIN_CLOSED_LINK_REUSE=1 GAMBIT_GENERATED_C_IN_PROCESS_DIGESTS=1
    export GAMBIT_DARWIN_CLOSED_LINK_FRESH_OBJECTS=1 GAMBIT_DARWIN_STATIC_OBJECT_REUSE=1
    export GAMBIT_DARWIN_NATIVE_OBJECT_CAPTURE=1 GAMBIT_DARWIN_NATIVE_OBJECT_CHECK=1 GAMBIT_DARWIN_BOUND_SINGLE_PASS=1
    if test "$pipeline" = recipe; then
      unset GAMBIT_DARWIN_CLOSED_LINK_FRESH_OBJECTS
      export GAMBIT_DARWIN_CLOSED_LINK_PRODUCER_PROOF=1 GAMBIT_DARWIN_CLOSED_LINK_RECIPE_PROOF=1
      proof_copy="(copy-file \"$workspace/lib/static/entry.o.gambit-static-proof\" \"$workspace/producer.proof\")"
    fi
  fi
  expression="(import :gerbil/compiler :gerbil/compiler/base)
    (def opts [output-dir: \"$workspace/lib\" output-file: \"$workspace/entry\"
               parallel: #t verbose: #t invoke-gsc: #t static: #t])
    (compile-module \"$workspace/entry.ss\" opts)
    (add-compile-dependent-job! [\"$workspace/lib/entry~0.c\"]
      (lambda ()
        (copy-file \"$workspace/lib/static/entry.o\" \"$workspace/producer.o\")
        $proof_copy
        (compile-exe \"$workspace/entry.ss\" $consume_opts)))
    (execute-pending-compile-jobs!)"
  if test "$role" = original; then
    "$home/bin/gerbil" interactive -e "$expression" > "$workspace/build.log" 2> "$workspace/backend.log"
  else
    "$home/bin/gxi" -e "$expression" > "$workspace/build.log" 2> "$workspace/backend.log"
  fi
  "$workspace/entry" > "$workspace/native.stdout"
  if test "$mode" = steady; then
    cmp "$workspace/producer.o" "$workspace/lib/static/entry.o"
    calls=1
    if test "$role:$pipeline" = candidate:recipe; then
      calls=2
      cmp "$workspace/producer.proof" "$workspace/lib/static/entry.o.gambit-static-proof"
      rg -q '^GAMBIT-STATIC-OBJECT-HIT$' "$workspace/backend.log"
    fi
    test "$(rg -c -- ' -obj .*[/]entry[.]c[)]' "$workspace/build.log")" = "$calls"
  elif test "$role:$pipeline" = candidate:recipe; then
    if cmp -s "$workspace/producer.o" "$workspace/lib/static/entry.o"; then exit 42; fi
  fi
  printf '%s ' "$role"
  cat "$workspace/native.stdout"
done
if test "$mode:$pipeline" != options-change:recipe; then
  cmp "$output/original/native.stdout" "$output/candidate/native.stdout"
fi
rg -q 'GAMBIT-CLOSED-LINK-SELECTED' "$output/candidate/build.log"
(
  cd "$output"
  shasum -a 256 original/native.stdout candidate/native.stdout \
    original/producer.o original/lib/static/entry.o \
    candidate/producer.o candidate/lib/static/entry.o
) > "$output/identity.log"
for role in original candidate; do
  role_expected=$expected
  if test "$role:$mode:$pipeline" = original:options-change:recipe; then role_expected=PRODUCER-MODE=17; fi
  if test "$(cat "$output/$role/native.stdout")" != "$role_expected"; then
    printf 'PRODUCER-MODE-DENY %s expected=%s mode=%s\n' "$role" "$role_expected" "$mode" >&2
    exit 42
  fi
done
if test "$mode:$pipeline" = options-change:recipe; then
  printf 'PRODUCER-RECIPE-OPTIONS-OK old-reference=17 new-consumer=29\n'
else
  printf 'PRODUCER-MODE-PARITY-OK ordinary-and-candidate-native-results-match\n'
fi
