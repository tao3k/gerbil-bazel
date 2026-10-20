#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../../.." && pwd)
if test "${1-}" = --batch; then
  shift
  bin=${1:?}; output=${2:?}; mode=${3:?}; count=${4:?}
  cd "$output"
  unset GAMBIT_DARWIN_STATIC_OBJECT_REUSE
  case "$mode" in
    control) ;;
    candidate) export GAMBIT_DARWIN_STATIC_OBJECT_REUSE=1 ;;
    *) exit 2 ;;
  esac
  for ((i=0; i<count; i++)); do
    rm -f -- module.o module.o.gambit-static-proof
    "$bin/gsc" -obj module.c
    cmp reference.o module.o
    test ! -e module.o.gambit-static-proof
    test ! -e module.o.gambit-static-lock
  done
  exit 0
fi
bin=${1:?isolated bin required}
output=${2:?fresh output required}
source=${3:?actual generated C required}
count=${4:-8}
case "$bin:$output:$source" in "$root"/.data/*:"$root"/.data/*:"$root"/.data/*) ;; *) exit 2 ;; esac
case "$count" in ''|*[!0-9]*) exit 2 ;; esac
test "$count" -gt 0 && test "$count" -le 100
test ! -e "$output"
mkdir -p "$output"
cp "$source" "$output/module.c"
home=$(cd "$bin/.." && pwd)
export GERBIL_HOME="$home"
export GAMBOPT="~~bin=$bin,~~lib=$home/lib,~~include=$home/include"
export PATH="/opt/homebrew/bin:/usr/bin:/bin:$PATH"
cd "$output"
unset GAMBIT_DARWIN_STATIC_OBJECT_REUSE
"$bin/gsc" -obj module.c > reference.log 2>&1
cp module.o reference.o
/usr/bin/shasum -a 256 module.c reference.o "$bin/gambuild-C" \
  "$bin/gambit-static-object-reuse" > identity.sha256
printf 'COLD-FALLBACK-ABBA count=%s\n' "$count"
index=0
for mode in control candidate candidate control; do
  index=$((index+1))
  /usr/bin/time -p -o "$output/$index-$mode.time" bash "$0" --batch \
    "$bin" "$output" "$mode" "$count" > "$index-$mode.log" 2>&1
  if rg -q 'GAMBIT-STATIC-OBJECT-(HIT|MISS)' "$index-$mode.log"; then exit 1; fi
  printf 'COLD-FALLBACK-ROUND %s %s\n' "$index" "$mode"
  cat "$index-$mode.time"
done
printf 'COLD-FALLBACK-COST-OK %s\n' "$((4*count))"
