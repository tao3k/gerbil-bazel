#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../../.." && pwd)
bin=${1:?owned compiled producer bin required}
runtime=${2:?owned matching runtime required}
source=${3:?owned paired Scheme/C directory required}
output=${4:?fresh owned receipt required}
case "$bin:$runtime:$source:$output" in "$root"/.data/*:"$root"/.data/*:"$root"/.data/*:"$root"/.data/*) ;; *) exit 2 ;; esac
cmp "$bin/../include/gambit.h" "$runtime/include/gambit.h"
test ! -e "$output"
mkdir -p "$output/inputs"
trap 'status=$?; printf "%s\n" "$status" > "$output/exit-status.txt"' EXIT
count=0
for input in "$source"/*.scm; do
  if test ! -f "$input" || test -L "$input"; then exit 2; fi
  test -f "${input%.scm}.c" || continue
  name=${input##*/}
  case "$name" in *$'\n'*) exit 2 ;; esac
  cp "$input" "$output/inputs/$name"
  printf '%s\n' "$name" >> "$output/inputs.txt"
  count=$((count+1))
done
test "$count" -gt 0
export CLOSED_COST_DIRECTORY="$output/inputs" CLOSED_COST_RECEIPT="$output"
export CLOSED_COST_INPUTS="$output/inputs.txt" CLOSED_COST_HASH_TOOL="$bin/gambit-file-sha256"
export CLOSED_COST_PROBE="$root/patches/gerbil-v19-darwin/tests/gambit-generated-c-closed-cost.scm"
export GAMBOPT="~~bin=$bin,~~lib=$runtime/lib,~~include=$runtime/include"
export GAMBIT_DARWIN_NATIVE_GENERATED_C=1 GAMBIT_GENERATED_C_BATCH_DIGESTS=1
export GAMBIT_GENERATED_C_IN_PROCESS_DIGESTS=1
unset GAMBIT_GENERATED_C_PRODUCER_INDEX
shasum -a 256 "$bin/gsc" "$CLOSED_COST_PROBE" > "$output/identity.log"
/usr/bin/time -p -o "$output/time.txt" "$bin/gsc" \
  -e '(load (getenv "CLOSED_COST_PROBE"))' -e '(run-closed-generation-cost!)' \
  > "$output/output.log" 2>&1
rg -q '^GAMBIT-GENERATED-C-MISS$' "$output/output.log"
rg -q '^GAMBIT-GENERATED-C-HIT$' "$output/output.log"
rg '^CLOSED-GENERATION-' "$output/output.log"
cat "$output/time.txt"
scms=(); cs=(); pins=()
while IFS= read -r name; do
  scms+=("$output/inputs/$name")
  cs+=("$output/inputs/${name%.scm}.c")
done < "$output/inputs.txt"
while IFS= read -r path; do
  case "$path" in "$output"/.gambit-c-*/*.c) ;; *) exit 2 ;; esac
  if test ! -f "$path" || test -L "$path"; then exit 2; fi
  pins+=("$path")
done < "$output/pinned-inputs.txt"
test "${#scms[@]}" -gt 0 && test "${#scms[@]}" = "${#pins[@]}"
unset GAMBIT_DARWIN_NATIVE_GENERATED_C GAMBIT_GENERATED_C_BATCH_DIGESTS
unset GAMBIT_GENERATED_C_IN_PROCESS_DIGESTS
export GAMBOPT="~~bin=$runtime/bin,~~lib=$runtime/lib,~~include=$runtime/include"
shasum -a 256 "${cs[@]}" > "$output/api-C.sha256"
"$runtime/bin/gsc" -link -flat -o "$output/closure.c" "${scms[@]}" > "$output/link-scheme.log" 2>&1
shasum -a 256 "${cs[@]}" > "$output/cli-C.sha256"
cmp "$output/api-C.sha256" "$output/cli-C.sha256"
cp "$output/closure.c" "$output/reference-link.c"
"$runtime/bin/gsc" -link -flat -o "$output/closure.c" "${pins[@]}" > "$output/link-pins.log" 2>&1
cmp "$output/reference-link.c" "$output/closure.c"
shasum -a 256 "$output/closure.c" > "$output/link.sha256"
printf 'CLOSED-GENERATION-COST-OK exact-C-parity populated-and-HIT\n'
printf 'CLOSED-GENERATION-SCHEME-PINNED-LINK-PARITY-OK\n'
