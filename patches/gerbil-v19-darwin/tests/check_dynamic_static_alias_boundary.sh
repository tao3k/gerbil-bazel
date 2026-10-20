#!/usr/bin/env bash
set -euo pipefail
compiler=${1:?compiler required}
input=${2:?actual generated Scheme input required}
alias=${3:?static module alias required}
output=${4:?fresh owned output required}
root=$(cd "$(dirname "$0")/../../.." && pwd)
case "$compiler:$input:$output" in "$root"/.data/*:"$root"/.data/*:"$root"/.data/*) ;; *) exit 2 ;; esac
test ! -e "$output"
test -f "$input"
test -x "$compiler"
mkdir -p "$output/dynamic" "$output/static"
stem=$(basename "${input%.scm}")
unset GAMBIT_DARWIN_NATIVE_GENERATED_C GAMBIT_GENERATED_C_PRODUCER_INDEX
"$compiler" -c -target C -module-ref "$alias" -linker-name "$stem.o1" \
  -o "$output/dynamic/$stem.c" "$input" > "$output/dynamic.log" 2>&1
"$compiler" -c -target C -module-ref "$alias" -linker-name "$alias" \
  -o "$output/static/$stem.c" "$input" > "$output/static.log" 2>&1
if cmp -s "$output/dynamic/$stem.c" "$output/static/$stem.c"; then
  printf 'ALIAS-BOUNDARY-UNEXPECTED-PARITY\n'
  exit 1
fi
shasum -a 256 "$compiler" "$input" "$output/dynamic/$stem.c" "$output/static/$stem.c" \
  > "$output/identity.log"
printf 'ALIAS-BOUNDARY-OK ordinary-dynamic-C-is-not-static-C\n'
