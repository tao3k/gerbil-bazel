#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../../.." && pwd)
bin=${1:?owned candidate bin required}
output=${2:?fresh owned receipt required}
home=${3:?owned matching toolchain home required}
case "$bin:$output:$home" in "$root"/.data/*:"$root"/.data/*:"$root"/.data/*) ;; *) exit 2 ;; esac
test ! -e "$output"
mkdir "$output"
trap 'status=$?; printf "%s\n" "$status" > "$output/exit-status.txt"' EXIT
export GERBIL_HOME="$home" GAMBOPT="~~bin=$bin,~~lib=$home/lib,~~include=$home/include"
export PATH="$bin:/opt/homebrew/bin:/usr/bin:/bin:$PATH"
unset GAMBIT_DARWIN_STATIC_OBJECT_REUSE GAMBIT_DARWIN_STATIC_EXPECTED_SOURCE_SHA
cd "$output"
printf 'int bound_probe(void) { return 17; }\n' > probe.c
"$bin/gsc" -obj probe.c > ordinary.log 2>&1
cp probe.o ordinary.o
expected=$("$bin/gambit-file-sha256" --raw probe.c)
export GAMBIT_DARWIN_STATIC_EXPECTED_SOURCE_SHA=${expected%% *}
export GAMBIT_DARWIN_BOUND_COLD_CAPTURE=1
rm probe.o
"$bin/gsc" -obj probe.c > cold.log 2>&1
rg -q '^GAMBIT-STATIC-BOUND-COLD-CAPTURE$' cold.log
cmp ordinary.o probe.o
test ! -e probe.o.gambit-static-proof
"$bin/gsc" -obj probe.c > populate.log 2>&1
rg -q '^GAMBIT-STATIC-OBJECT-MISS$' populate.log
cmp ordinary.o probe.o
"$bin/gsc" -obj probe.c > hit.log 2>&1
rg -q '^GAMBIT-STATIC-OBJECT-HIT$' hit.log
cmp ordinary.o probe.o
cp probe.o.gambit-static-proof selected.proof
rm probe.o
printf 'int bound_probe(void) { return 29; }\n' > probe.c
if "$bin/gsc" -obj probe.c > mismatch.log 2>&1; then exit 1; fi
rg -q '^GAMBIT-STATIC-BOUND-SOURCE-DENY$' mismatch.log
test ! -e probe.o
cmp selected.proof probe.o.gambit-static-proof
printf 'int bound_probe(void) { return 17; }\n' > probe.c
"$bin/gsc" -obj probe.c > concurrent-a.log 2>&1 &
first=$!
"$bin/gsc" -obj probe.c > concurrent-b.log 2>&1 &
second=$!
status=0
wait "$first" || status=1
wait "$second" || status=1
test "$status" = 0
test "$(rg --no-filename '^GAMBIT-STATIC-BOUND-COLD-CAPTURE$' concurrent-a.log concurrent-b.log | wc -l | tr -d ' ')" = 1
test "$(rg --no-filename '^GAMBIT-STATIC-OBJECT-MISS$' concurrent-a.log concurrent-b.log | wc -l | tr -d ' ')" = 1
cmp ordinary.o probe.o
"$bin/gsc" -obj probe.c > concurrent-hit.log 2>&1
rg -q '^GAMBIT-STATIC-OBJECT-(HIT|MISS)$' concurrent-hit.log
cmp ordinary.o probe.o
# Background and foreground invocations need not have identical environments.
"$bin/gsc" -obj probe.c > foreground-hit.log 2>&1
rg -q '^GAMBIT-STATIC-OBJECT-HIT$' foreground-hit.log
test ! -e probe.o.gambit-static-lock
printf 'BOUND-COLD-CAPTURE-OK exact-object no-cold-proof full-later-validation source-rejection concurrency\n'
