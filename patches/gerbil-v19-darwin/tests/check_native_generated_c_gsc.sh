#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../../.." && pwd)
bin=${1:?owned candidate bin required}
runtime=${2:?owned matching runtime required}
output=${3:?fresh owned fixture required}
case "$bin:$runtime:$output" in "$root"/.data/*:"$root"/.data/*:"$root"/.data/*) ;; *) exit 2 ;; esac
test ! -e "$output"
mkdir -p "$output" "$output/index"
export PATH="/opt/homebrew/bin:/usr/bin:/bin:$PATH"
export GAMBOPT="~~bin=$bin,~~lib=$runtime/lib,~~include=$runtime/include"
export GAMBIT_GENERATED_C_PRODUCER_INDEX="$output/index"
input="$output/module.scm"
c="$output/module.c"
printf '(define (answer) 17)\n' > "$input"
cp "$input" "$output/producer-alias.scm"
args=(-c -o "$c" -target C -module-ref producer-alias -linker-name producer-alias "$input")
"$runtime/bin/gsc" "${args[@]}" > "$output/original.log" 2>&1
cp "$c" "$output/original.c"
"$bin/gsc" "${args[@]}" > "$output/default.log" 2>&1
cmp "$c" "$output/original.c"
test ! -e "$c.generation-proof"
export GAMBIT_DARWIN_NATIVE_GENERATED_C=1 GAMBIT_GENERATED_C_BATCH_DIGESTS=1
case "${4:-all-producers}" in
  all-producers) ;;
  planned-producers)
    "$bin/gsc" "${args[@]}" > "$output/unrequested.log" 2>&1
    cmp "$c" "$output/original.c"
    test ! -e "$c.generation-proof"
    args=(-generated-c-proof "${args[@]}") ;;
  *) exit 2 ;;
esac
"$bin/gsc" "${args[@]}" > "$output/miss.log" 2>&1
rg -q '^GAMBIT-GENERATED-C-MISS$' "$output/miss.log"
cmp "$c" "$output/original.c"
"$bin/gsc" "${args[@]}" > "$output/hit.log" 2>&1
rg -q '^GAMBIT-GENERATED-C-HIT$' "$output/hit.log"
cmp "$c" "$output/original.c"
test ! -e "$c.generation-proof.lock"
test "$(stat -f '%Lp' "$c.generation-proof")" = 600
if test "${GAMBIT_GENERATED_C_IN_PROCESS_DIGESTS-}" = 1; then
  unset GAMBIT_GENERATED_C_IN_PROCESS_DIGESTS
  "$bin/gsc" "${args[@]}" > "$output/backend-disabled.log" 2>&1
  rg -q '^GAMBIT-GENERATED-C-MISS$' "$output/backend-disabled.log"
  cmp "$c" "$output/original.c"
  export GAMBIT_GENERATED_C_IN_PROCESS_DIGESTS=1
  "$bin/gsc" "${args[@]}" > "$output/backend-restored.log" 2>&1
  rg -q '^GAMBIT-GENERATED-C-MISS$' "$output/backend-restored.log"
  cmp "$c" "$output/original.c"
fi
"$runtime/bin/gsc" -link -target C -o "$output/closure.c" "$output/producer-alias.scm" > "$output/link-original.log" 2>&1
cp "$output/closure.c" "$output/original-closure.c"
"$bin/gsc" -link -target C -o "$output/closure.c" "$output/producer-alias.scm" > "$output/link-native.log" 2>&1
rg -q '^GAMBIT-NATIVE-PRODUCED-C-LINK-HIT 1$' "$output/link-native.log"
cmp "$output/closure.c" "$output/original-closure.c"
printf '(define (answer) 29)\n' > "$output/producer-alias.scm"
"$runtime/bin/gsc" -link -target C -o "$output/closure.c" "$output/producer-alias.scm" > "$output/link-changed-original.log" 2>&1
cp "$output/closure.c" "$output/changed-closure.c"
"$bin/gsc" -link -target C -o "$output/closure.c" "$output/producer-alias.scm" > "$output/link-changed-native.log" 2>&1
if rg -q '^GAMBIT-NATIVE-PRODUCED-C-LINK-HIT' "$output/link-changed-native.log"; then exit 1; fi
cmp "$output/closure.c" "$output/changed-closure.c"
cp "$input" "$output/producer-alias.scm"
"$runtime/bin/gsc" -link -debug-source -target C -o "$output/closure.c" "$output/producer-alias.scm" > "$output/link-debug-original.log" 2>&1
cp "$output/closure.c" "$output/debug-closure.c"
"$bin/gsc" -link -debug-source -target C -o "$output/closure.c" "$output/producer-alias.scm" > "$output/link-debug-native.log" 2>&1
if rg -q '^GAMBIT-NATIVE-PRODUCED-C-LINK-HIT' "$output/link-debug-native.log"; then exit 1; fi
cmp "$output/closure.c" "$output/debug-closure.c"
cp "$output/index/producer-alias.producer" "$output/saved-producer"
printf 'invalid-record\n' > "$output/index/producer-alias.producer"
"$bin/gsc" -link -target C -o "$output/closure.c" "$output/producer-alias.scm" > "$output/link-invalid-index.log" 2>&1
if rg -q '^GAMBIT-NATIVE-PRODUCED-C-LINK-HIT' "$output/link-invalid-index.log"; then exit 1; fi
cmp "$output/closure.c" "$output/original-closure.c"
cp "$output/saved-producer" "$output/index/producer-alias.producer"
before=$(shasum -a 256 "$c.generation-proof")
printf '(define (answer)\n' > "$input"
if "$bin/gsc" "${args[@]}" > "$output/failure.log" 2>&1; then exit 1; fi
cmp "$c" "$output/original.c"
test "$before" = "$(shasum -a 256 "$c.generation-proof")"
test ! -e "$c.generation-proof.lock"
for path in "$c".generation-work-*; do test ! -e "$path"; done
printf 'NATIVE-GENERATED-C-GSC-CONTRACT-OK default-parity cold-parity cross-process-hit native-link-adoption link-parity changed-static-fallback debug-fallback invalid-index-fallback failure-preservation cleanup\n'
