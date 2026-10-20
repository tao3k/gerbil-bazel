#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../../.." && pwd)
bin=${1:?owned native candidate bin required}
runtime=${2:?owned matching runtime required}
source=${3:?owned paired static source required}
output=${4:?fresh owned output required}
policy=${5:-all-producers}
case "$policy" in all-producers|planned-producers) ;; *) exit 2 ;; esac
case "$bin:$runtime:$source:$output" in "$root"/.data/*:"$root"/.data/*:"$root"/.data/*:"$root"/.data/*) ;; *) exit 2 ;; esac
test ! -e "$output"
mkdir -p "$output/source" "$output/dynamic" "$output/published" "$output/original" "$output/lookup" "$output/index"
export PATH="/opt/homebrew/bin:/usr/bin:/bin:$PATH"
export GAMBOPT="~~bin=$bin,~~lib=$runtime/lib,~~include=$runtime/include"
export GAMBIT_DARWIN_NATIVE_GENERATED_C=1 GAMBIT_GENERATED_C_BATCH_DIGESTS=1
export GAMBIT_GENERATED_C_PRODUCER_INDEX="$output/index"
export GENERATION_FIXTURE="$output" GENERATION_BIN="$bin"
export GENERATION_LOOKUP="$root/patches/gerbil-v19-darwin/tests/native_produced_c_lookup.scm"
inputs=()
for path in "$source"/*.scm; do
  test -f "$path" && test ! -L "$path"
  test -f "${path%.scm}.c" || continue
  copy="$output/source/$(basename "$path")"
  cp "$path" "$copy"
  cp "$path" "$output/dynamic/producer-${#inputs[@]}.scm"
  inputs+=("$copy")
done
test "${#inputs[@]}" = 55
printf '%s\n' "${inputs[@]}" > "$output/ordered-inputs.txt"
produce() {
  local compiler=$1 mode=$2 index alias c
  local request=()
  if test "$mode" = native && test "$policy" = planned-producers; then request=(-generated-c-proof); fi
  for ((index=0; index<${#inputs[@]}; index++)); do
    alias=$(basename "${inputs[index]}" .scm)
    c="$output/published/producer-$index.c"
    "$compiler" "${request[@]}" -c -o "$c" -target C -module-ref "$alias" -linker-name "$alias" \
      "$output/dynamic/producer-$index.scm" > "$output/$mode-$index.log" 2>&1
    if test "$mode" = original; then
      cp "$c" "$output/original/producer-$index.c"
    else
      cmp "$c" "$output/original/producer-$index.c"
      test -f "$c.generation-proof"
      rg -q '^GAMBIT-GENERATED-C-MISS$' "$output/$mode-$index.log"
      test ! -e "$c.generation-proof.lock"
      for work in "$c".generation-work-*; do test ! -e "$work"; done
    fi
  done
}
{ time -p produce "$runtime/bin/gsc" original; } 2> "$output/original-produce.time"
{ time -p produce "$bin/gsc" native; } 2> "$output/native-produce.time"
"$bin/gsc" -e '(load (getenv "GENERATION_LOOKUP"))' -e '(run-native-produced-c-lookup!)' > "$output/lookup.log" 2>&1
pins=()
while IFS= read -r path; do
  case "$path" in "$output"/.gambit-c-*/*.c) ;; *) exit 2 ;; esac
  pins+=("$path")
done < "$output/pinned-inputs.txt"
test "${#pins[@]}" = 55
{ time -p "$runtime/bin/gsc" -link -target C -o "$output/closure.c" "${inputs[@]}" > "$output/original-link.log" 2>&1; } 2> "$output/original-link.time"
cp "$output/closure.c" "$output/original-closure.c"
{ time -p "$bin/gsc" -link -target C -o "$output/closure.c" "${inputs[@]}" > "$output/native-link.log" 2>&1; } 2> "$output/native-link.time"
rg -q '^GAMBIT-NATIVE-PRODUCED-C-LINK-HIT 55$' "$output/native-link.log"
cmp "$output/closure.c" "$output/original-closure.c"
cat "$output/original-produce.time" "$output/native-produce.time" "$output/lookup.log" "$output/original-link.time" "$output/native-link.time"
printf 'REAL-NATIVE-GENERATED-C-GSC-OK 55 producer-byte-parity native-link-adoption link-byte-parity\n'
