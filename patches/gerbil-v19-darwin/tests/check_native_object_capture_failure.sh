#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../../.." && pwd)
original=${1:?owned native-capture candidate bin required}
output=${2:?fresh owned output required}
home=${3:?matching runtime home required}
case "$original:$output:$home" in "$root"/.data/*:"$root"/.data/*:"$root"/.data/*) ;; *) exit 2 ;; esac
test ! -e "$output"
mkdir -p "$output/bin" "$output/work"
trap 'status=$?; printf "%s\n" "$status" > "$output/exit-status.txt"' EXIT
bin="$output/bin"
cp "$original/gambit-file-sha256" "$original/gambit-static-object-reuse" "$bin/"
for tool in gsc gxi gerbil; do ln -s "$original/$tool" "$bin/$tool"; done
printf '%s\n' '#!/bin/sh' \
  '/opt/homebrew/bin/gcc-16 "$@"' 'status=$?' \
  'if test "${NATIVE_CAPTURE_MUTATE_TOOL-}" = 1; then' \
  '  for arg in "$@"; do if test "$arg" = -c; then' \
  '    printf "\nprivate-native-capture-mutation\n" >> "$NATIVE_CAPTURE_BIN/gambit-file-sha256"' \
  '    printf "TOOL-MUTATION-EXECUTED\n" >> "$NATIVE_CAPTURE_BIN/mutations.log"' \
  '  fi; done' 'fi' 'exit "$status"' > "$bin/compiler"
chmod +x "$bin/compiler"
sed "s|/opt/homebrew/bin/gcc-16|$bin/compiler|g" "$original/gambuild-C" > "$bin/gambuild-C"
chmod +x "$bin/gambuild-C"
export GERBIL_HOME="$home" GAMBOPT="~~bin=$bin,~~lib=$home/lib,~~include=$home/include"
export NATIVE_CAPTURE_BIN="$bin"
export GAMBIT_DARWIN_NATIVE_OBJECT_CAPTURE=1 GAMBIT_DARWIN_BOUND_SINGLE_PASS=1
unset GAMBIT_DARWIN_STATIC_OBJECT_REUSE GAMBIT_DARWIN_STATIC_EXPECTED_SOURCE_SHA NATIVE_CAPTURE_MUTATE_TOOL
cd "$output/work"
printf 'int failure_probe(void) { return 17; }\n' > probe.c
cp probe.c valid.c
"$bin/gsc" -obj probe.c > ordinary.log 2>&1
cp probe.o ordinary.o
printf 'int failure_probe(void) { not valid C; }\n' > probe.c
export GAMBIT_DARWIN_STATIC_EXPECTED_SOURCE_SHA=$("$bin/gambit-file-sha256" --raw probe.c)
if "$bin/gsc" -obj probe.c > compile-failure.log 2>&1; then exit 1; fi
rg -q 'error:' compile-failure.log
cmp ordinary.o probe.o
test ! -e probe.o.gambit-static-proof
cp valid.c probe.c
export GAMBIT_DARWIN_STATIC_EXPECTED_SOURCE_SHA=$("$bin/gambit-file-sha256" --raw probe.c)
export NATIVE_CAPTURE_MUTATE_TOOL=1
if "$bin/gsc" -obj probe.c > tool-mutation.log 2>&1; then exit 1; fi
rg -q '^TOOL-MUTATION-EXECUTED$' "$bin/mutations.log"
cmp ordinary.o probe.o
test ! -e probe.o.gambit-static-proof
unset NATIVE_CAPTURE_MUTATE_TOOL
"$bin/gsc" -obj probe.c > recovery.log 2>&1
rg -q '^GAMBIT-STATIC-BOUND-NATIVE-CAPTURE$' recovery.log
cmp ordinary.o probe.o
"$bin/gsc" -obj probe.c > hit.log 2>&1
rg -q '^GAMBIT-STATIC-OBJECT-HIT$' hit.log
shopt -s nullglob
leftovers=(probe.o.gambit-static.* probe.c.gambit-static.*)
test "${#leftovers[@]}" = 0
test ! -e probe.o.gambit-static-lock
printf 'NATIVE-CAPTURE-FAILURE-OK compiler-failure tool-change-during-compile old-object-preserved proof-not-published recovery-HIT cleanup\n'
