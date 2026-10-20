#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../../.." && pwd)
bin=${1:?isolated compiler bin required}
runtime=${2:?matching owned runtime required}
source=${3:?owned paired source directory required}
output=${4:?fresh output required}
case "$bin:$runtime:$source:$output" in "$root"/.data/*:"$root"/.data/*:"$root"/.data/*:"$root"/.data/*) ;; *) exit 2 ;; esac
cmp "$bin/gsc" "$runtime/bin/gsc"
test ! -e "$output"
mkdir -p "$output/source" "$output/dynamic" "$output/published" "$output/work" "$output/lookup"
inputs=()
for path in "$source"/*.scm; do
  test -f "$path" && test ! -L "$path"
  test -f "${path%.scm}.c" || continue
  cp "$path" "$output/source/$(basename "$path")"
  inputs+=("$output/source/$(basename "$path")")
done
test "${#inputs[@]}" = 55
printf '%s\n' "${inputs[@]}" > "$output/ordered-inputs.txt"
export PATH="/opt/homebrew/bin:/usr/bin:/bin:$PATH"
export GAMBOPT="~~bin=$bin,~~lib=$runtime/lib,~~include=$runtime/include"
export GENERATION_FIXTURE="$output" GENERATION_BIN="$bin"
export GENERATION_JOURNAL="$root/patches/gerbil-v19-darwin/tests/gambit-generated-c-reads.scm"
export GENERATION_IMPLEMENTATION="$root/patches/gerbil-v19-darwin/tests/gambit-generated-c-closure.scm"
export GENERATION_CONTRACT="$root/patches/gerbil-v19-darwin/tests/real_produced_generated_c.scm"
"$bin/gsc" -e '(load (getenv "GENERATION_JOURNAL"))' \
  -e '(load (getenv "GENERATION_IMPLEMENTATION"))' \
  -e '(load (getenv "GENERATION_CONTRACT"))' \
  -e '(run-real-produced-generated-c!)' > "$output/output.log" 2>&1
pinned=()
while IFS= read -r path; do
  case "$path" in "$output"/.gambit-c-*/*.c) ;; *) exit 2 ;; esac
  pinned+=("$path")
done < "$output/pinned-inputs.txt"
test "${#pinned[@]}" = 55
/usr/bin/time -p -o "$output/original-link.time" "$bin/gsc" -link -target C -o "$output/closure.c" "${inputs[@]}" > "$output/original-link.log" 2>&1
cp "$output/closure.c" "$output/original-closure.c"
/usr/bin/time -p -o "$output/adopted-link.time" "$bin/gsc" -link -target C -o "$output/closure.c" "${pinned[@]}" > "$output/adopted-link.log" 2>&1
cmp "$output/original-closure.c" "$output/closure.c"
cat "$output/output.log" "$output/original-link.time" "$output/adopted-link.time"
printf 'REAL-PRODUCED-C-LINK-PARITY-OK 55\n'
