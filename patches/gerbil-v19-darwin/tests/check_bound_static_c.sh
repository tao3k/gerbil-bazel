#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../../.." && pwd)
bin=${1:?owned bound-input candidate bin required}
output=${2:?fresh owned receipt required}
home=${3:?owned matching toolchain home required}
case "$bin:$output:$home" in "$root"/.data/*:"$root"/.data/*:"$root"/.data/*) ;; *) exit 2 ;; esac
test -f "$home/include/gambit.h" && test ! -L "$home/include/gambit.h"
test ! -e "$output"
mkdir -p "$output"
trap 'status=$?; printf "%s\n" "$status" > "$output/exit-status.txt"' EXIT
export GERBIL_HOME="$home"
export GAMBOPT="~~bin=$bin,~~lib=$home/lib,~~include=$home/include"
cd "$output"
printf 'int bound_probe(void) { return 17; }\n' > probe.c
cp probe.c selected.c
unset GAMBIT_DARWIN_STATIC_OBJECT_REUSE GAMBIT_DARWIN_STATIC_EXPECTED_SOURCE_SHA
"$bin/gsc" -obj probe.c > ordinary.log 2>&1
cp probe.o ordinary.o
expected=$("$bin/gambit-file-sha256" --raw selected.c)
export GAMBIT_DARWIN_STATIC_EXPECTED_SOURCE_SHA=${expected%% *}
rm probe.o
"$bin/gsc" -obj probe.c > cold.log 2>&1
rg -q '^GAMBIT-STATIC-OBJECT-MISS$' cold.log
cmp ordinary.o probe.o
"$bin/gsc" -obj probe.c > hit.log 2>&1
rg -q '^GAMBIT-STATIC-OBJECT-HIT$' hit.log
cp probe.o.gambit-static-proof selected.proof
printf 'int bound_probe(void) { return 29; }\n' > probe.c
for state in existing missing; do
  if test "$state" = missing; then rm probe.o; fi
  if "$bin/gsc" -obj probe.c > "$state-mismatch.log" 2>&1; then exit 1; fi
  rg -q '^GAMBIT-STATIC-BOUND-SOURCE-DENY$' "$state-mismatch.log"
  cmp selected.proof probe.o.gambit-static-proof
  if test "$state" = existing; then cmp ordinary.o probe.o; else test ! -e probe.o; fi
done
cp selected.c probe.c
"$bin/gsc" -obj probe.c > recovery.log 2>&1
cmp ordinary.o probe.o
cp probe.o.gambit-static-proof selected.proof
if "$bin/gsc" -obj -cc-options '-g' probe.c > unsupported.log 2>&1; then exit 1; fi
rg -q '^GAMBIT-STATIC-BOUND-UNSUPPORTED-DENY$' unsupported.log
cmp ordinary.o probe.o
cmp selected.proof probe.o.gambit-static-proof
for digest in '' short $(printf '%064d' 0)g; do
  if GAMBIT_DARWIN_STATIC_EXPECTED_SOURCE_SHA="$digest" "$bin/gsc" -obj probe.c > invalid.log 2>&1; then exit 1; fi
  rg -q '^GAMBIT-STATIC-BOUND-DIGEST-DENY$' invalid.log
  cmp ordinary.o probe.o
  cmp selected.proof probe.o.gambit-static-proof
done
rm probe.o
"$bin/gsc" -obj probe.c > concurrent-a.log 2>&1 &
first=$!
"$bin/gsc" -obj probe.c > concurrent-b.log 2>&1 &
second=$!
trap 'kill "$first" "$second" 2>/dev/null || true; wait "$first" 2>/dev/null || true; wait "$second" 2>/dev/null || true' ERR
wait "$first"
wait "$second"
trap - ERR
test "$(rg --no-filename '^GAMBIT-STATIC-OBJECT-MISS$' concurrent-a.log concurrent-b.log | wc -l | tr -d ' ')" = 1
test "$(rg --no-filename '^GAMBIT-STATIC-OBJECT-HIT$' concurrent-a.log concurrent-b.log | wc -l | tr -d ' ')" = 1
cmp ordinary.o probe.o
test ! -e probe.o.gambit-static-lock
printf 'BOUND-STATIC-C-OK cold HIT source-rejection recovery unsupported invalid-digest concurrency\n'
