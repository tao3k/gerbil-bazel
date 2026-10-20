#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../../.." && pwd)
bin=${1:?isolated compiler bin required}
runtime=${2:?matching owned runtime required}
output=${3:?fresh output required}
case "$bin:$runtime:$output" in "$root"/.data/*:"$root"/.data/*:"$root"/.data/*) ;; *) exit 2 ;; esac
cmp "$bin/gsc" "$runtime/bin/gsc"
test ! -e "$output"
mkdir -p "$output/published" "$output/produce" "$output/lookup"
export PATH="/opt/homebrew/bin:/usr/bin:/bin:$PATH"
export GAMBOPT="~~bin=$bin,~~lib=$runtime/lib,~~include=$runtime/include"
export GENERATION_FIXTURE="$output" GENERATION_BIN="$bin"
export GENERATION_JOURNAL="$root/patches/gerbil-v19-darwin/tests/gambit-generated-c-reads.scm"
export GENERATION_IMPLEMENTATION="$root/patches/gerbil-v19-darwin/tests/gambit-generated-c-closure.scm"
export GENERATION_CONTRACT="$root/patches/gerbil-v19-darwin/tests/produced_generated_c_contract.scm"
"$bin/gsc" -e '(load (getenv "GENERATION_JOURNAL"))' \
  -e '(load (getenv "GENERATION_IMPLEMENTATION"))' \
  -e '(load (getenv "GENERATION_CONTRACT"))' \
  -e '(run-produced-generated-c-contract!)' > "$output/output.log" 2>&1
IFS= read -r pinned < "$output/pinned-input.txt"
"$bin/gsc" -link -target C -o "$output/closure.c" "$output/producer-alias.scm" > "$output/link-original.log" 2>&1
cp "$output/closure.c" "$output/original-closure.c"
"$bin/gsc" -link -target C -o "$output/closure.c" "$pinned" > "$output/link-adopted.log" 2>&1
cmp "$output/original-closure.c" "$output/closure.c"
cat "$output/output.log"
printf 'PRODUCED-GENERATED-C-LINK-PARITY-OK\n'
