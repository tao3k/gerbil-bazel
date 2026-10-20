#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../../.." && pwd)
bin=${1:?owned candidate bin required}
output=${2:?fresh owned receipt required}
home=${3:?owned matching toolchain home required}
binding_mode=${4:-ordinary}
case "$binding_mode" in ordinary|bound-single-pass) ;; *) exit 2 ;; esac
case "$bin:$output:$home" in "$root"/.data/*:"$root"/.data/*:"$root"/.data/*) ;; *) exit 2 ;; esac
test -f "$home/include/gambit.h" && test ! -L "$home/include/gambit.h"
test ! -e "$output"
mkdir -p "$output/nested"
trap 'status=$?; printf "%s\n" "$status" > "$output/exit-status.txt"' EXIT
export GERBIL_HOME="$home"
export GAMBOPT="~~bin=$bin,~~lib=$home/lib,~~include=$home/include"
cd "$output"
printf '%s\n' '#define HEADER_VALUE 17' \
  'const char *header_filename = __FILE__;' \
  'int header_level = __INCLUDE_LEVEL__;' > nested/inner.h
printf '%s\n' '#include "inner.h"' > nested/outer.h
printf '%s\n' '#include "outer.h"' \
  'const char *source_filename = __FILE__;' \
  'const char *base_filename = __BASE_FILE__;' \
  'const char *short_filename = __FILE_NAME__;' \
  'const char *source_timestamp = __TIMESTAMP__;' \
  'int source_line = __LINE__;' \
  'int source_level = __INCLUDE_LEVEL__;' \
  'int snapshot_probe(void) { return HEADER_VALUE; }' > nested/probe.c
touch -t 202001010000 nested/probe.c
for mode in plain debug prefix-map; do
  options=''
  case "$mode" in debug) options='-g' ;; prefix-map) options='-g -ffile-prefix-map=nested=logical' ;; esac
  unset GAMBIT_DARWIN_STATIC_OBJECT_REUSE GAMBIT_DARWIN_STATIC_EXPECTED_SOURCE_SHA
  "$bin/gsc" -obj -cc-options "$options" nested/probe.c > "$mode-control.log" 2>&1
  cp nested/probe.o "$mode-control.o"
  export GAMBIT_DARWIN_STATIC_OBJECT_REUSE=1
  if test "$binding_mode:$mode" = bound-single-pass:plain; then
    expected=$("$bin/gambit-file-sha256" --raw nested/probe.c)
    export GAMBIT_DARWIN_STATIC_EXPECTED_SOURCE_SHA=${expected%% *}
    export GAMBIT_DARWIN_BOUND_SINGLE_PASS=1
  fi
  "$bin/gsc" -obj -cc-options "$options" nested/probe.c > "$mode-candidate.log" 2>&1
  cmp "$mode-control.o" nested/probe.o
  if test "$mode" != plain; then
    cmp "$mode-control.log" "$mode-candidate.log"
    test ! -e nested/probe.o.gambit-static-proof
  else
    if test "$binding_mode" = bound-single-pass; then
      rg -q '^GAMBIT-STATIC-BOUND-SINGLE-PASS$' "$mode-candidate.log"
    fi
    rg -q '^GAMBIT-STATIC-OBJECT-MISS$' "$mode-candidate.log"
    "$bin/gsc" -obj -cc-options "$options" nested/probe.c > "$mode-repeat.log" 2>&1
    rg -q '^GAMBIT-STATIC-OBJECT-HIT$' "$mode-repeat.log"
    cmp "$mode-control.o" nested/probe.o
  fi
done
printf 'STATIC-SNAPSHOT-SEMANTICS-OK relative-headers filename-macros timestamp lines debug-and-prefix-map-fallback\n'
