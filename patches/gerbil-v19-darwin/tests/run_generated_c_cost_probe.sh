#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../../.." && pwd)
bin=${1:?owned native compiler bin required}
runtime=${2:?owned matching runtime required}
source=${3:?owned paired generated Scheme directory required}
output=${4:?fresh owned diagnostic receipt required}
case "$bin:$runtime:$source:$output" in "$root"/.data/*:"$root"/.data/*:"$root"/.data/*:"$root"/.data/*) ;; *) exit 2 ;; esac
test ! -e "$output"
mkdir -p "$output/inputs" "$output/index"
trap 'status=$?; printf "%s\n" "$status" > "$output/exit-status.txt"' EXIT
for input in "$source"/*.scm; do
  test -f "$input" && test ! -L "$input"
  test -f "${input%.scm}.c" || continue
  cp "$input" "$output/inputs/$(basename "$input")"
  basename "$input" >> "$output/inputs.txt"
done
export GSC_COST_DIRECTORY="$output/inputs/" GSC_COST_INPUTS="$output/inputs.txt"
export GSC_COST_PROBE="$root/patches/gerbil-v19-darwin/tests/gambit-generated-c-cost-probe.scm"
export GAMBOPT="~~bin=$bin,~~lib=$runtime/lib,~~include=$runtime/include"
export GAMBIT_DARWIN_NATIVE_GENERATED_C=1 GAMBIT_GENERATED_C_BATCH_DIGESTS=1
export GAMBIT_GENERATED_C_IN_PROCESS_DIGESTS=1 GAMBIT_GENERATED_C_PRODUCER_INDEX="$output/index"
shasum -a 256 "$bin/gsc" "$GSC_COST_PROBE" > "$output/identity.log"
/usr/bin/time -p -o "$output/time.txt" "$bin/gsc" \
  -e '(load (getenv "GSC_COST_PROBE"))' -e '(run-generation-cost-probe!)' \
  > "$output/output.log" 2>&1
rg '^GENERATION-COST' "$output/output.log"
cat "$output/time.txt"
export GAMBOPT="~~bin=$runtime/bin,~~lib=$runtime/lib,~~include=$runtime/include"
while IFS= read -r name; do
  alias=${name%.scm}
  c="$output/inputs/$alias.c"
  cp "$c" "$c.probed"
  "$runtime/bin/gsc" -c -o "$c" -target C -module-ref "$alias" -linker-name "$alias" \
    "$output/inputs/$name" > "$output/original-$alias.log" 2>&1
  cmp "$c" "$c.probed"
done < "$output/inputs.txt"
printf 'GENERATION-COST-PARITY-OK all-probed-C-matches-original\n'
