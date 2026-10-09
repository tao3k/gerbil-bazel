#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../../.." && pwd)
bin=${1:?isolated driver bin required}
output=${2:?fresh output required}
home=${3:-"$root/.data/d1391-runtime-object-source/build"}
source=${4:-"$root/.data/ascent-link-regeneration-v4/core__types.c"}
case "$output:$source" in "$root"/.data/*:"$root"/.data/*) ;; *) exit 2 ;; esac
# Selected installed tools are read-only inputs; only owned output is written.
test -d "$bin" && test ! -L "$bin"
test -d "$home" && test ! -L "$home"
if test ! -f "$home/include/gambit.h" || test -L "$home/include/gambit.h"; then exit 2; fi
if test ! -f "$source" || test -L "$source"; then exit 2; fi
test ! -e "$output"
mkdir -p "$output"
cp "$source" "$output/module.c"
shasum -a 256 "$home/include/gambit.h" "$bin/gsc" > "$output/selected-toolchain.sha256"
export GERBIL_HOME="$home"
export GAMBOPT="~~bin=$bin,~~lib=$home/lib,~~include=$home/include"
cd "$output"
unset GAMBIT_DARWIN_STATIC_OBJECT_REUSE
"$bin/gsc" -obj module.c > control.log 2>&1
cp module.o control.o
export GAMBIT_DARWIN_STATIC_OBJECT_REUSE=1
"$bin/gsc" -obj module.c > first.log 2>&1
cmp control.o module.o
rg -q '^GAMBIT-STATIC-OBJECT-MISS$' first.log
"$bin/gsc" -obj module.c > repeat.log 2>&1
cmp control.o module.o
rg -q '^GAMBIT-STATIC-OBJECT-HIT$' repeat.log
"$bin/gsc" -obj -cc-options '-O2' module.c > options.log 2>&1
if rg -q 'warning:' options.log; then
  if rg -q '^GAMBIT-STATIC-OBJECT-HIT$' options.log; then exit 1; fi
else
  rg -q '^GAMBIT-STATIC-OBJECT-MISS$' options.log
fi
cp module.o options.o
unset GAMBIT_DARWIN_STATIC_OBJECT_REUSE
"$bin/gsc" -obj -cc-options '-O2' module.c > options-control.log 2>&1
cmp options.o module.o
if rg -q 'warning:' options.log; then cmp options.log options-control.log; fi
export GAMBIT_DARWIN_STATIC_OBJECT_REUSE=1
printf 'tampered-object\n' > module.o
"$bin/gsc" -obj -cc-options '-O2' module.c > tamper.log 2>&1
if rg -q '^GAMBIT-STATIC-OBJECT-HIT$' tamper.log; then exit 1; fi
cmp options.o module.o
if rg -q 'warning:' options-control.log; then cmp tamper.log options-control.log; fi
"$bin/gsc" -obj module.c > concurrent-establish.log 2>&1
cmp control.o module.o
"$bin/gsc" -obj module.c > concurrent-a.log 2>&1 &
first=$!
"$bin/gsc" -obj module.c > concurrent-b.log 2>&1 &
second=$!
wait "$first"
wait "$second"
test "$(rg -c '^GAMBIT-STATIC-OBJECT-(HIT|MISS)$' concurrent-a.log)" = 1
test "$(rg -c '^GAMBIT-STATIC-OBJECT-(HIT|MISS)$' concurrent-b.log)" = 1
rg -q '^GAMBIT-STATIC-OBJECT-HIT$' concurrent-a.log concurrent-b.log
cmp control.o module.o
printf '#define VALUE 17\n' > probe.h
printf '#include "probe.h"\nint probe(void) { return VALUE; }\n' > probe.c
"$bin/gsc" -obj probe.c > header-cold.log 2>&1
"$bin/gsc" -obj probe.c > header-first.log 2>&1
"$bin/gsc" -obj probe.c > header-hit.log 2>&1
rg -q '^GAMBIT-STATIC-OBJECT-HIT$' header-hit.log
cp probe.o header-before.o
printf '#define VALUE 29\n' > probe.h
"$bin/gsc" -obj probe.c > header-change.log 2>&1
rg -q '^GAMBIT-STATIC-OBJECT-MISS$' header-change.log
if cmp -s header-before.o probe.o; then exit 1; fi
cp probe.o header-after.o
unset GAMBIT_DARWIN_STATIC_OBJECT_REUSE
"$bin/gsc" -obj probe.c > header-control.log 2>&1
cmp header-after.o probe.o
export GAMBIT_DARWIN_STATIC_OBJECT_REUSE=1
cp probe.o before-failure.o
cp probe.o.gambit-static-proof before-failure.proof
printf '#include "probe.h"\nint probe(void) { invalid C syntax; }\n' > probe.c
if "$bin/gsc" -obj probe.c > failure.log 2>&1; then exit 1; fi
cmp before-failure.o probe.o
cmp before-failure.proof probe.o.gambit-static-proof
test ! -d probe.o.gambit-static-lock
printf 'STATIC-OBJECT-REUSE-OK 8\n'
