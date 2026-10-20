#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../../.." && pwd)
base=${1:?owned 0029 source required}
compiled=${2:?owned role-aware native source required}
output=${3:?fresh owned replay fixture required}
case "$base:$compiled:$output" in "$root"/.data/*:"$root"/.data/*:"$root"/.data/*) ;; *) exit 2 ;; esac
test ! -e "$output"
files=(gsc/_gsc.scm gsi/main.scm gsc/gambit-generated-c-closed-link.scm)
for file in "${files[@]}"; do
  test -f "$base/$file"; test ! -L "$base/$file"
  test -f "$compiled/$file"; test ! -L "$compiled/$file"
done
mkdir -p "$output/source/gsc" "$output/source/gsi"
cd "$output/source"
git init -q
for file in "${files[@]}"; do cp "$base/$file" "$file"; done
git add gsc gsi
for file in "${files[@]}"; do cp "$compiled/$file" "$file"; done
git diff -- gsc gsi > "$output/closed-link-role.patch"
test -s "$output/closed-link-role.patch"
git apply --reverse --check "$output/closed-link-role.patch"
git apply --reverse "$output/closed-link-role.patch"
for file in "${files[@]}"; do cmp "$base/$file" "$file"; done
git apply --check "$output/closed-link-role.patch"
git apply "$output/closed-link-role.patch"
for file in "${files[@]}"; do cmp "$compiled/$file" "$file"; done
shasum -a 256 ../closed-link-role.patch "${files[@]}" > "$output/identity.log"
printf 'CLOSED-LINK-ROLE-PATCH-REPLAY-OK original-reverse role-aware-forward exact-source-parity\n'
