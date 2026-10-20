#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../../.." && pwd)
runtime=${1:?owned Gambit runtime required}
output=${2:?fresh owned fixture required}
case "$runtime:$output" in "$root"/.data/*:"$root"/.data/*) ;; *) exit 2 ;; esac
test "$(uname -s)" = Darwin
test ! -e "$output"
mkdir -p "$output/individual" "$output/grouped"
trap 'status=$?; printf "%s\n" "$status" > "$output/exit-status.txt"' EXIT
tests="$root/patches/gerbil-v19-darwin/tests"
cp "$tests/bundle_alpha.scm" "$output/alpha.scm"
cp "$tests/bundle_beta.scm" "$output/beta.scm"
cp "$tests/bundle_image_counter.scm" "$output/counter.scm"
export GAMBOPT="~~bin=$runtime/bin,~~lib=$runtime/lib,~~include=$runtime/include"
export SDKROOT="$(/usr/bin/xcrun --sdk macosx --show-sdk-path)"
export BUNDLE_FIXTURE="$output" BUNDLE_CONTRACT="$tests/gambit_multi_entry_bundle_contract.scm"
unset GAMBIT_DARWIN_NATIVE_GENERATED_C GAMBIT_DARWIN_STATIC_OBJECT_REUSE GAMBIT_DARWIN_NATIVE_OBJECTS
for name in alpha beta counter; do
  "$runtime/bin/gsc" -c -target C -module-ref "$name" -linker-name "$name.o1" \
    -o "$output/$name.c" "$output/$name.scm" > "$output/$name-generate.log" 2>&1
done
link() {
  local target=$1
  shift
  local inputs
  printf -v inputs '%s\n' "$@"
  env BUILD_DYN_INPUT_FILENAMES_PARAM="$inputs" BUILD_DYN_OUTPUT_FILENAME_PARAM="$output/$target.o1" \
    GAMBITDIR_INCLUDE="$runtime/include" GAMBITDIR_LIB="$runtime/lib" \
    BUILD_DYN_CC_OPTIONS_PARAM="-isysroot $SDKROOT" \
    BUILD_DYN_LD_OPTIONS_PARAM="-Wl,-undefined,dynamic_lookup" \
    "$runtime/bin/gambuild-C" dyn > "$output/$target-link.log" 2>&1
}
for name in alpha beta counter; do link "$name" "$output/$name.c"; done
link combined "$output/alpha.c" "$output/beta.c"
for name in alpha beta; do
  ln -s "../$name.o1" "$output/individual/$name.o1"
  ln -s '../combined.o1' "$output/grouped/$name.o1"
done
for mode in individual grouped; do
  for order in forward reverse; do
    export BUNDLE_MODE="$mode" BUNDLE_ORDER="$order"
    "$runtime/bin/gsc" -e '(load (getenv "BUNDLE_CONTRACT"))' \
      -e '(run-multi-entry-bundle-contract!)' > "$output/$mode-$order.log" 2>&1
    cat "$output/$mode-$order.log"
  done
done
printf 'MULTI-ENTRY-BUNDLE-CONTRACT-OK four-fresh-processes default-loader init-order mutable-state missing-entry repeat-rejection image-count\n'
