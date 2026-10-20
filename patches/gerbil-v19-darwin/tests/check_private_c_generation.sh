#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../../.." && pwd)
bin=${1:?isolated native compiler bin required}
source=${2:?owned paired static source directory required}
output=${3:?fresh output required}
case "$bin:$source:$output" in "$root"/.data/*:"$root"/.data/*:"$root"/.data/*) ;; *) exit 2 ;; esac
test ! -e "$output"
mkdir -p "$output/source" "$output/private"
inputs=(); names=()
for path in "$source"/*.scm; do
  test -f "$path" && test ! -L "$path"
  if test ! -f "${path%.scm}.c"; then continue; fi
  name=$(basename "$path")
  cp "$path" "$output/source/$name"
  inputs+=("$output/source/$name")
  names+=("${name%.scm}")
done
test "${#inputs[@]}" -gt 1
home=$(cd "$bin/.." && pwd)
export GERBIL_HOME="$home"
export GAMBOPT="~~bin=$bin,~~lib=$home/lib,~~include=$home/include"
export PATH="/opt/homebrew/bin:/usr/bin:/bin:$PATH"
cd "$output"
/usr/bin/shasum -a 256 "$bin/gsc" > compiler.sha256
/usr/bin/shasum -a 256 "${inputs[@]}" > sources-before.sha256
"$bin/gsc" -link -flat -o closure.c "${inputs[@]}" > original.log 2>&1
cp closure.c reference-link.c
"$bin/gsc" -c -o "$output/private/" "${inputs[@]}" > private.log 2>&1
cs=()
for name in "${names[@]}"; do
  cmp "$output/source/$name.c" "$output/private/$name.c"
  cs+=("$output/private/$name.c")
done
"$bin/gsc" -link -flat -o closure.c "${cs[@]}" > private-link.log 2>&1
cmp reference-link.c closure.c
/usr/bin/shasum -a 256 "${inputs[@]}" > sources-after.sha256
cmp sources-before.sha256 sources-after.sha256
printf 'PRIVATE-C-GENERATION-PARITY-OK modules=%s\n' "${#inputs[@]}"
