#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../../.." && pwd)
bin=${1:?owned candidate bin required}
output=${2:?fresh owned receipt required}
home=${3:?owned matching toolchain home required}
control=${4:-modes}
case "$control" in modes|compiler-prefix) ;; *) exit 2 ;; esac
case "$bin:$output:$home" in "$root"/.data/*:"$root"/.data/*:"$root"/.data/*) ;; *) exit 2 ;; esac
test ! -e "$output"
mkdir "$output"
trap 'status=$?; printf "%s\n" "$status" > "$output/exit-status.txt"' EXIT
export GERBIL_HOME="$home" GAMBOPT="~~bin=$bin,~~lib=$home/lib,~~include=$home/include"
export PATH="$bin:/opt/homebrew/bin:/usr/bin:/bin:$PATH"
export GAMBIT_DARWIN_BOUND_SINGLE_PASS=1
cd "$output"
if test "$control" = compiler-prefix; then
  printf '%s\n' '#ifndef COMPILER_PREFIX_VALUE' '#define COMPILER_PREFIX_VALUE 17' '#endif' \
    'int compiler_prefix_probe(void) { return COMPILER_PREFIX_VALUE; }' > probe.c
  export GAMBITDIR_INCLUDE="$home/include"
  export BUILD_OBJ_INPUT_FILENAMES_PARAM=probe.c BUILD_OBJ_OUTPUT_FILENAME_PARAM=probe.o
  export BUILD_OBJ_META_INFO_FILE_PARAM=probe.c BUILD_OBJ_CC_OPTIONS_PARAM=''
  export BUILD_OBJ_CC_PARAM='/opt/homebrew/bin/gcc-16 -ftrack-macro-expansion=0 -DCOMPILER_PREFIX_VALUE=29'
  unset GAMBIT_DARWIN_STATIC_OBJECT_REUSE GAMBIT_DARWIN_STATIC_EXPECTED_SOURCE_SHA
  unset GAMBIT_DARWIN_NATIVE_OBJECT_CAPTURE GAMBIT_DARWIN_NATIVE_OBJECT_CHECK
  "$bin/gambuild-C" obj > compiler-prefix-reference.log 2>&1
  cp probe.o compiler-prefix-reference.o
  rm probe.o
  export GAMBIT_DARWIN_STATIC_EXPECTED_SOURCE_SHA=$("$bin/gambit-file-sha256" --raw probe.c)
  export GAMBIT_DARWIN_NATIVE_OBJECT_CAPTURE=1 GAMBIT_DARWIN_NATIVE_OBJECT_CHECK=1
  for phase in population hit; do
    "$bin/gambuild-C" obj > "compiler-prefix-$phase.log" 2>&1
    if ! cmp -s compiler-prefix-reference.o probe.o; then
      printf 'COMPILER-PREFIX-DENY actual-object-differs-from-declared-compiler-recipe\n' >&2
      exit 42
    fi
    if test "$phase" = hit; then rg -q '^GAMBIT-STATIC-OBJECT-HIT$' "compiler-prefix-$phase.log"; fi
  done
  export BUILD_OBJ_CC_PARAM='/opt/homebrew/bin/gcc-16 -ftrack-macro-expansion=0 -DCOMPILER_PREFIX_VALUE=31'
  env -u GAMBIT_DARWIN_STATIC_EXPECTED_SOURCE_SHA \
    BUILD_OBJ_OUTPUT_FILENAME_PARAM=compiler-prefix-change-reference.o \
    "$bin/gambuild-C" obj > compiler-prefix-change-reference.log 2>&1
  for phase in change change-hit; do
    "$bin/gambuild-C" obj > "compiler-prefix-$phase.log" 2>&1
    cmp compiler-prefix-change-reference.o probe.o
    if test "$phase" = change; then
      rg -q '^GAMBIT-STATIC-OBJECT-MISS$' "compiler-prefix-$phase.log"
    else
      rg -q '^GAMBIT-STATIC-OBJECT-HIT$' "compiler-prefix-$phase.log"
    fi
  done
  printf 'COMPILER-PREFIX-OK native-population-HIT change-MISS-repeat-HIT exact-declared-recipe-parity\n'
  exit 0
fi
printf '%s\n' '#ifdef ___DYNAMIC' 'int mode_probe(void) { return 17; }' \
  '#else' 'int mode_probe(void) { return 29; }' '#endif' > probe.c
expected=$("$bin/gambit-file-sha256" --raw probe.c)
for mode in dynamic static; do
  options=''
  if test "$mode" = dynamic; then options='-D___DYNAMIC -fPIC'; fi
  unset GAMBIT_DARWIN_STATIC_OBJECT_REUSE GAMBIT_DARWIN_STATIC_EXPECTED_SOURCE_SHA
  "$bin/gsc" -obj -cc-options "$options" probe.c > "$mode-reference.log" 2>&1
  cp probe.o "$mode-reference.o"
done
if cmp -s dynamic-reference.o static-reference.o; then exit 1; fi
export GAMBIT_DARWIN_STATIC_EXPECTED_SOURCE_SHA=${expected%% *}
for phase in dynamic-population dynamic-hit static-change static-hit dynamic-return dynamic-return-hit; do
  options='-D___DYNAMIC -fPIC'
  mode=dynamic
  case "$phase" in static-*) options=''; mode=static ;; esac
  "$bin/gsc" -obj -cc-options "$options" probe.c > "$phase.log" 2>&1
  cmp "$mode-reference.o" probe.o
  case "$phase" in
    *hit) rg -q '^GAMBIT-STATIC-OBJECT-HIT$' "$phase.log" ;;
    *) rg -q '^GAMBIT-STATIC-OBJECT-MISS$' "$phase.log" ;;
  esac
done
rg -q '^GAMBIT-STATIC-BOUND-SINGLE-PASS$' dynamic-population.log
printf 'BOUND-OBJECT-MODES-OK identical-source different-object mode-change-MISS matching-mode-HIT exact-parity\n'
