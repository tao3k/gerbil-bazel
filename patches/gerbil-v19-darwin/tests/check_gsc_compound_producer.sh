#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../../.." && pwd)
bin=${1:?owned GSC bin required}
home=${2:?matching runtime home required}
source=${3:?real compiled module SCM required}
output=${4:?fresh owned receipt required}
case "$bin:$home:$source:$output" in "$root"/.data/*:"$root"/.data/*:"$root"/.data/*:"$root"/.data/*) ;; *) exit 2 ;; esac
test ! -e "$output"
mkdir -p "$output/work"
trap 'status=$?; printf "%s\n" "$status" > "$output/exit-status.txt"' EXIT
cp -p "$source" "$output/work/module.scm"
export GERBIL_HOME="$home" GAMBOPT="~~bin=$bin,~~lib=$home/lib,~~include=$home/include"
export PATH="$bin:/opt/homebrew/bin:/usr/bin:/bin:$PATH"
unset GAMBIT_DARWIN_STATIC_OBJECT_REUSE GAMBIT_DARWIN_STATIC_EXPECTED_SOURCE_SHA
unset GAMBIT_DARWIN_BOUND_SINGLE_PASS GAMBIT_DARWIN_NATIVE_OBJECT_CAPTURE GAMBIT_DARWIN_NATIVE_OBJECT_CHECK
unset CC CFLAGS CPPFLAGS LDFLAGS CPATH C_INCLUDE_PATH CPLUS_INCLUDE_PATH
unset NIX_CFLAGS_COMPILE NIX_LDFLAGS SDKROOT DEVELOPER_DIR
export GAMBIT_COMPOUND_SOURCE="$output/work/module.scm"
export GAMBIT_COMPOUND_RUNTIME_C="$output/work/runtime.c"
export GAMBIT_COMPOUND_STATIC_C="$output/work/static.c"
export GAMBIT_COMPOUND_STATIC_O="$output/work/static.o"
export GAMBIT_COMPOUND_MODULE_REF=compound_binary_relation
export GAMBIT_COMPOUND_CC_OPTIONS="-D___DYNAMIC -fPIC -I $home/lib/static"
export GAMBIT_COMPOUND_HELPER="$root/patches/gerbil-v19-darwin/tests/gambit_compound_producer.scm"
cd "$output/work"
for phase in ordinary-1 compound-1 compound-2 ordinary-2; do
  case "$phase" in
    ordinary-*)
      /usr/bin/time -p -o "$output/$phase-generate.time" "$bin/gsc" -c -o "$GAMBIT_COMPOUND_RUNTIME_C" \
        -module-ref "$GAMBIT_COMPOUND_MODULE_REF" -linker-name "$GAMBIT_COMPOUND_MODULE_REF" \
        "$GAMBIT_COMPOUND_SOURCE" > "$output/$phase.log" 2>&1
      if test -e "$GAMBIT_COMPOUND_STATIC_C"; then rm "$GAMBIT_COMPOUND_STATIC_C"; fi
      cp "$GAMBIT_COMPOUND_RUNTIME_C" "$GAMBIT_COMPOUND_STATIC_C"
      /usr/bin/time -p -o "$output/$phase-object.time" "$bin/gsc" -obj -o "$GAMBIT_COMPOUND_STATIC_O" \
        -cc-options "$GAMBIT_COMPOUND_CC_OPTIONS" "$GAMBIT_COMPOUND_STATIC_C" >> "$output/$phase.log" 2>&1 ;;
    *)
      /usr/bin/time -p -o "$output/$phase.time" "$bin/gsc" \
        -e '(load (getenv "GAMBIT_COMPOUND_HELPER"))' > "$output/$phase.log" 2>&1
      rg -q '^GAMBIT-COMPOUND-PRODUCER-OK$' "$output/$phase.log" ;;
  esac
  cp "$GAMBIT_COMPOUND_RUNTIME_C" "$output/$phase.c"
  cp "$GAMBIT_COMPOUND_STATIC_O" "$output/$phase.o"
  cmp "$output/ordinary-1.c" "$output/$phase.c"
  cmp "$output/ordinary-1.o" "$output/$phase.o"
done
printf 'GSC-COMPOUND-PRODUCER-OK ABBA real-module exact-C-object-parity two-GSC-calls-to-one\n'
