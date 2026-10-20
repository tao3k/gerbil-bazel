#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../../.." && pwd)
home=${1:?owned candidate compiler home required}
output=${2:?fresh receipt directory required}
native=${3:-}
metadata=${4:-}
case "$home:$output" in "$root"/.data/*:"$root"/.data/*) ;; *) exit 2 ;; esac
test ! -e "$output"
test -x "$home/bin/gxi"
mkdir "$output"
trap 'status=$?; printf "%s\n" "$status" > "$output/exit-status.txt"' EXIT
export GERBIL_HOME="$home" GERBIL_GSC="$home/bin/gsc"
export GERBIL_PATH="$output/prefix" GERBIL_LOADPATH="$home/lib"
binary="$home/bin/gxi"
arguments=("$root/patches/gerbil-v19-darwin/tests/compiler-output-recipe-contract.ss")
if test -n "$native"; then
  case "$native:$metadata" in "$root"/.data/*:"$root"/.data/*) ;; *) exit 2 ;; esac
  test -f "$native" && test ! -L "$native" && test -x "$native"
  test -f "$metadata/gerbil/compiler/base.ssi"
  binary="$native"
  export GERBIL_LOADPATH="$metadata:$home/lib"
  # The metadata supplies exports/macros, never a substitute executor image.
  arguments=(-e "(def native-names '(gxc#open-compile-executor gxc#add-compile-output-job! gxc#current-compile-output-recipe))
    (def native-procedures (map ##eval native-names))
    (unless (andmap procedure? native-procedures) (error \"AOT executor not initialized\"))
    (load \"$root/patches/gerbil-v19-darwin/tests/compiler-output-recipe-contract.ss\")
    (unless (andmap eq? native-procedures (map ##eval native-names))
      (error \"AOT executor overwritten by dynamic image\"))
    (displayln \"AOT-EXECUTOR-IDENTITY-OK\")")
elif test -n "$metadata"; then
  exit 2
fi
export GAMBOPT="~~bin=$home/bin,~~lib=$home/lib,~~include=$home/include"
export GERBIL_BUILD_CORES="$(getconf NPROCESSORS_ONLN)"
test "$GERBIL_BUILD_CORES" -ge 2
command -v gtimeout >/dev/null
for mode in disabled enabled; do
  unset GAMBIT_DARWIN_CLOSED_LINK_RECIPE_PROOF
  expected='#f'
  if test "$mode" = enabled; then
    export GAMBIT_DARWIN_CLOSED_LINK_RECIPE_PROOF=1
    expected='#t'
  fi
  /usr/bin/time -p -o "$output/$mode.time" gtimeout --signal=TERM --kill-after=1 30s "$binary" \
    "${arguments[@]}" \
    > "$output/$mode.log" 2>&1
  rg -q "^PRODUCER-RECIPE-LIFECYCLE-OK enabled=$expected$" "$output/$mode.log"
  if test -n "$native"; then rg -q '^AOT-EXECUTOR-IDENTITY-OK$' "$output/$mode.log"; fi
  cat "$output/$mode.log"
done
(
  cd "$root"
  if test -n "$native"; then
    shasum -a 256 "${native#"$root/"}" "${metadata#"$root/"}/gerbil/compiler/base.ssi"
  else
    shasum -a 256 "${home#"$root/"}/lib/gerbil/compiler/base~0.o1" \
      "${home#"$root/"}/lib/gerbil/compiler/driver~0.o1"
  fi
  shasum -a 256 patches/gerbil-v19-darwin/tests/compiler-output-recipe-contract.ss
) > "$output/identity.log"
printf 'PRODUCER-RECIPE-LIFECYCLE-CONTROLS-OK worker-count=%s\n' "$GERBIL_BUILD_CORES"
