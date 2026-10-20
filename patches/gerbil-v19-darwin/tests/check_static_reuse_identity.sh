#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../../.." && pwd)
original=${1:?isolated driver bin required}
output=${2:?fresh output required}
home=${3:-"$root/.data/d1391-runtime-object-source/build"}
case "$original:$output" in "$root"/.data/*:"$root"/.data/*) ;; *) exit 2 ;; esac
case "$home" in "$root"/.data/*) ;; *) exit 2 ;; esac
if test ! -f "$home/include/gambit.h" || test -L "$home/include/gambit.h"; then exit 2; fi
test ! -e "$output"
mkdir -p "$output/bin" "$output/work"
cp "$original/gambuild-C" "$original/gambit-static-object-reuse" "$output/bin/"
if test -x "$original/gambit-file-sha256"; then cp "$original/gambit-file-sha256" "$output/bin/"; fi
for tool in gsc gxi gerbil; do ln -s "$original/$tool" "$output/bin/$tool"; done
bin="$output/bin"
shasum -a 256 "$home/include/gambit.h" "$original/gsc" > "$output/selected-toolchain.sha256"
export GERBIL_HOME="$home"
export GAMBOPT="~~bin=$bin,~~lib=$home/lib,~~include=$home/include"
export GAMBIT_DARWIN_STATIC_OBJECT_REUSE=1
cd "$output/work"
printf 'int identity_probe(void) { return 17; }\n' > probe.c
"$bin/gsc" -obj probe.c > cold.log 2>&1
"$bin/gsc" -obj probe.c > establish.log 2>&1
"$bin/gsc" -obj probe.c > hit.log 2>&1
rg -q '^GAMBIT-STATIC-OBJECT-HIT$' hit.log
cp probe.o original.o
printf 'int identity_probe(void) { return 29; }\n' > probe.c
"$bin/gsc" -obj probe.c > source-change.log 2>&1
rg -q '^GAMBIT-STATIC-OBJECT-MISS$' source-change.log
if cmp -s original.o probe.o; then exit 1; fi
cp probe.o changed.o
unset GAMBIT_DARWIN_STATIC_OBJECT_REUSE
"$bin/gsc" -obj probe.c > source-control.log 2>&1
cmp changed.o probe.o
export GAMBIT_DARWIN_STATIC_OBJECT_REUSE=1
"$bin/gsc" -obj probe.c > source-repeat.log 2>&1
rg -q '^GAMBIT-STATIC-OBJECT-HIT$' source-repeat.log
printf '\n# Isolated identity invalidation control.\n' >> "$bin/gambit-static-object-reuse"
"$bin/gsc" -obj probe.c > helper-change.log 2>&1
rg -q '^GAMBIT-STATIC-OBJECT-MISS$' helper-change.log
cmp changed.o probe.o
"$bin/gsc" -obj probe.c > helper-repeat.log 2>&1
rg -q '^GAMBIT-STATIC-OBJECT-HIT$' helper-repeat.log
printf '\n# Isolated driver identity invalidation control.\n' >> "$bin/gambuild-C"
"$bin/gsc" -obj probe.c > driver-change.log 2>&1
rg -q '^GAMBIT-STATIC-OBJECT-MISS$' driver-change.log
cmp changed.o probe.o
"$bin/gsc" -obj probe.c > driver-repeat.log 2>&1
rg -q '^GAMBIT-STATIC-OBJECT-HIT$' driver-repeat.log
test ! -d probe.o.gambit-static-lock
printf 'STATIC-OBJECT-IDENTITY-OK 3\n'
