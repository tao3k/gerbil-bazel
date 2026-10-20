#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../../.." && pwd)
bin=${1:?isolated native compiler bin required}
source=${2:?owned static source directory required}
output=${3:?fresh output required}
candidate=${4:-}
case "$bin:$source:$output" in "$root"/.data/*:"$root"/.data/*:"$root"/.data/*) ;; *) exit 2 ;; esac
home=$(cd "$bin/.." && pwd)
if test -n "$candidate"; then
  case "$candidate" in "$root"/.data/*) ;; *) exit 2 ;; esac
  candidate_home=$(cd "$candidate/.." && pwd)
  cmp "$home/include/gambit.h" "$candidate_home/include/gambit.h"
fi
test ! -e "$output"
mkdir -p "$output"
scms=(); cs=()
for path in "$source"/*.scm; do
  test -f "$path" && test ! -L "$path"
  name=$(basename "$path")
  if test ! -f "${path%.scm}.c"; then
    printf '%s\n' "$name" >> "$output/unpaired-scheme-inputs.txt"
    continue
  fi
  cp "$path" "$output/$name"
  cp "${path%.scm}.c" "$output/${name%.scm}.c"
  scms+=("$name")
  cs+=("${name%.scm}.c")
done
test "${#scms[@]}" -gt 1
export GERBIL_HOME="$home"
export GAMBOPT="~~bin=$bin,~~lib=$home/lib,~~include=$home/include"
export PATH="/opt/homebrew/bin:/usr/bin:/bin:$PATH"
unset GAMBIT_DARWIN_NATIVE_GENERATED_C GAMBIT_GENERATED_C_BATCH_DIGESTS
unset GAMBIT_GENERATED_C_IN_PROCESS_DIGESTS GAMBIT_GENERATED_C_PRODUCER_INDEX
cd "$output"
/usr/bin/shasum -a 256 "$bin/gsc" > compiler.sha256
if test -n "$candidate"; then /usr/bin/shasum -a 256 "$candidate/gsc" > candidate.sha256; fi
/usr/bin/shasum -a 256 "${scms[@]}" > scheme-before.sha256
# First generation establishes this compiler's C output; copied C is not admitted.
"$bin/gsc" -link -flat -o closure.c "${scms[@]}" > establish.log 2>&1
cp closure.c reference-link.c
/usr/bin/shasum -a 256 "${cs[@]}" > generated-before.sha256
index=0
modes=(scheme c c scheme)
if test -n "$candidate"; then modes=(scheme native native scheme); fi
for mode in "${modes[@]}"; do
  index=$((index+1))
  run_bin=$bin
  if test "$mode" = native; then run_bin=$candidate; fi
  export GAMBOPT="~~bin=$run_bin,~~lib=$home/lib,~~include=$home/include"
  if test "$mode" = c; then inputs=("${cs[@]}"); else inputs=("${scms[@]}"); fi
  /usr/bin/time -p -o "$index-$mode.time" "$run_bin/gsc" -link -flat \
    -o closure.c "${inputs[@]}" > "$index-$mode.log" 2>&1
  cmp reference-link.c closure.c
  /usr/bin/shasum -a 256 "${cs[@]}" > generated-after.sha256
  cmp generated-before.sha256 generated-after.sha256
  printf 'STATIC-CLOSURE-GENERATION-ROUND %s %s\n' "$index" "$mode"
  cat "$index-$mode.time"
done
/usr/bin/shasum -a 256 "$bin/gsc" > compiler-after.sha256
cmp compiler.sha256 compiler-after.sha256
if test -n "$candidate"; then
  /usr/bin/shasum -a 256 "$candidate/gsc" > candidate-after.sha256
  cmp candidate.sha256 candidate-after.sha256
fi
/usr/bin/shasum -a 256 "${scms[@]}" > scheme-after.sha256
cmp scheme-before.sha256 scheme-after.sha256
for name in "${scms[@]}"; do cmp "$source/$name" "$name"; done
if test -n "$candidate"; then
  printf 'STATIC-CLOSURE-COMPILER-OFF-COST-OK modules=%s\n' "${#scms[@]}"
else
  printf 'STATIC-CLOSURE-GENERATION-COST-OK modules=%s\n' "${#scms[@]}"
fi
