#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../../.." && pwd)
bin=${1:?owned native compiler bin required}
runtime=${2:?owned matching runtime required}
output=${3:?fresh owned fixture required}
case "$bin:$runtime:$output" in "$root"/.data/*:"$root"/.data/*:"$root"/.data/*) ;; *) exit 2 ;; esac
test ! -e "$output"
mkdir -p "$output/index"
export GAMBOPT="~~bin=$bin,~~lib=$runtime/lib,~~include=$runtime/include"
export GAMBIT_DARWIN_NATIVE_GENERATED_C=1 GAMBIT_GENERATED_C_BATCH_DIGESTS=1
export GAMBIT_GENERATED_C_IN_PROCESS_DIGESTS=1 GAMBIT_GENERATED_C_PRODUCER_INDEX="$output/index"
input="$output/module.scm"
c="$output/module.c"
printf '(define (answer) 17)\n' > "$input"
common=(-c -o "$c" -target C -module-ref module -linker-name module "$input")
"$runtime/bin/gsc" "${common[@]}" > "$output/original.log" 2>&1
cp "$c" "$output/original.c"
"$bin/gsc" -generated-c-proof "${common[@]}" > "$output/first.log" 2>&1 &
first=$!
"$bin/gsc" -generated-c-proof "${common[@]}" > "$output/second.log" 2>&1 &
second=$!
first_status=0
second_status=0
wait "$first" || first_status=$?
wait "$second" || second_status=$?
printf '%s %s\n' "$first_status" "$second_status" > "$output/exit-status.txt"
test "$first_status" = 0 && test "$second_status" = 0
test "$(rg --no-filename '^GAMBIT-GENERATED-C-MISS$' "$output/first.log" "$output/second.log" | wc -l | tr -d ' ')" = 1
test "$(rg --no-filename '^GAMBIT-GENERATED-C-HIT$' "$output/first.log" "$output/second.log" | wc -l | tr -d ' ')" = 1
cmp "$c" "$output/original.c"
test ! -e "$c.generation-proof.lock"
test "$(/usr/bin/stat -f '%Lp' "$c.generation-proof")" = 600
test -f "$output/index/module.producer"
for work in "$c".generation-work-*; do test ! -e "$work"; done
printf 'NATIVE-GENERATED-C-CONCURRENCY-OK two-processes one-MISS one-HIT C-parity cleanup\n'
