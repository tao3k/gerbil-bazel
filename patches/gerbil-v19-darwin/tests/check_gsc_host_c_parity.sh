#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../../.." && pwd)
runtime_a=${1:?owned reference compiler runtime required}
runtime_b=${2:?owned alternative compiler runtime required}
source=${3:?owned paired generated Scheme directory required}
output=${4:?fresh owned receipt directory required}
case "$runtime_a:$runtime_b:$source:$output" in "$root"/.data/*:"$root"/.data/*:"$root"/.data/*:"$root"/.data/*) ;; *) exit 2 ;; esac
test "$(uname -s)" = Darwin
test ! -e "$output"
for runtime in "$runtime_a" "$runtime_b"; do
  test -x "$runtime/bin/gsc" && test ! -L "$runtime/bin/gsc"
done
mkdir -p "$output/inputs" "$output/published" "$output/reference"
trap 'status=$?; printf "%s\n" "$status" > "$output/exit-status.txt"' EXIT
unset GAMBIT_DARWIN_NATIVE_GENERATED_C GAMBIT_GENERATED_C_BATCH_DIGESTS
unset GAMBIT_GENERATED_C_IN_PROCESS_DIGESTS GAMBIT_GENERATED_C_PRODUCER_INDEX
inputs=()
for path in "$source"/*.scm; do
  test -f "$path" && test ! -L "$path"
  test -f "${path%.scm}.c" || continue
  name=$(basename "$path")
  cp "$path" "$output/inputs/$name"
  inputs+=("$name")
done
test "${#inputs[@]}" -gt 0
cd "$output"
printf '%s\n' "${inputs[@]}" > inputs.txt
shasum -a 256 inputs/*.scm > inputs.sha256
for label in a b; do
  runtime=$runtime_a
  test "$label" != b || runtime=$runtime_b
  shasum -a 256 "$runtime/bin/gsc" | awk -v label="$label" '{print $1, label}' >> compilers.sha256
  GAMBOPT="~~bin=$runtime/bin,~~lib=$runtime/lib,~~include=$runtime/include" \
    "$runtime/bin/gsc" -v > "$label-version.txt" 2>&1
done
produce() {
  local runtime=$1 round=$2 name alias
  export GAMBOPT="~~bin=$runtime/bin,~~lib=$runtime/lib,~~include=$runtime/include"
  for name in "${inputs[@]}"; do
    alias=${name%.scm}
    "$runtime/bin/gsc" -c -o "published/$alias.c" -target C \
      -module-ref "$alias" -linker-name "$alias" "inputs/$name" > "$round-$alias.log" 2>&1
    if test "$round" = a1; then
      cp "published/$alias.c" "reference/$alias.c"
    else
      if ! cmp "reference/$alias.c" "published/$alias.c"; then
        printf 'GSC-HOST-C-PARITY-DENY round=%s module=%s\n' "$round" "$alias" | tee parity-denied.txt
        exit 1
      fi
    fi
  done
}
for round in a1 b1 b2 a2; do
  runtime=$runtime_a
  case "$round" in b*) runtime=$runtime_b ;; esac
  { time -p produce "$runtime" "$round"; } 2> "$round-produce.time"
  cat "$round-produce.time"
  printf 'GSC-HOST-C-PARITY %s files=%s\n' "$round" "${#inputs[@]}"
done
link_inputs=()
for name in "${inputs[@]}"; do link_inputs+=("inputs/$name"); done
for label in a b; do
  runtime=$runtime_a
  test "$label" != b || runtime=$runtime_b
  export GAMBOPT="~~bin=$runtime/bin,~~lib=$runtime/lib,~~include=$runtime/include"
  { time -p "$runtime/bin/gsc" -link -target C -o closure.c "${link_inputs[@]}" > "$label-link.log" 2>&1; } 2> "$label-link.time"
  if test "$label" = a; then cp closure.c reference-closure.c; else cmp closure.c reference-closure.c; fi
  cat "$label-link.time"
done
shasum -a 256 reference/*.c reference-closure.c > generated.sha256
printf 'GSC-HOST-C-PARITY-OK files=%s ABBA whole-C-byte-parity link-byte-parity\n' "${#inputs[@]}"
