#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../../.." && pwd)
base=${1:?owned original Gambit source required}
compiled=${2:?owned prepared native GSC source required}
output=${3:?fresh owned replay fixture required}
case "$base:$compiled:$output" in "$root"/.data/*:"$root"/.data/*:"$root"/.data/*) ;; *) exit 2 ;; esac
test ! -e "$output"
files=(gambit-generated-c-reads.scm gambit-generated-c-closure.scm
       gambit-generated-c-native.scm gambit-generated-c-native-digest.scm
       gambit-generated-c-native-digest-install.scm
       gambit-generated-c-planned-producer.scm gambit-file-sha256.c)
for file in gsc/_gsc.scm gsi/main.scm; do
  test -f "$base/$file" && test ! -L "$base/$file"
  test -f "$compiled/$file" && test ! -L "$compiled/$file"
done
for file in "${files[@]}"; do
  test -f "$compiled/gsc/$file" && test ! -L "$compiled/gsc/$file"
done
mkdir -p "$output/source/gsc" "$output/source/gsi"
cd "$output/source"
git init -q
cp "$base/gsc/_gsc.scm" gsc/_gsc.scm
cp "$base/gsi/main.scm" gsi/main.scm
git add gsc/_gsc.scm gsi/main.scm
cp "$compiled/gsc/_gsc.scm" gsc/_gsc.scm
cp "$compiled/gsi/main.scm" gsi/main.scm
for file in "${files[@]}"; do cp "$compiled/gsc/$file" "gsc/$file"; done
git add --intent-to-add gsc
git diff -- gsc gsi > "$output/native-generated-c.patch"
test -s "$output/native-generated-c.patch"
git apply --reverse --check "$output/native-generated-c.patch"
git apply --reverse "$output/native-generated-c.patch"
cmp "$base/gsc/_gsc.scm" gsc/_gsc.scm
cmp "$base/gsi/main.scm" gsi/main.scm
for file in "${files[@]}"; do test ! -e "gsc/$file"; done
git apply --check "$output/native-generated-c.patch"
git apply "$output/native-generated-c.patch"
cmp "$compiled/gsc/_gsc.scm" gsc/_gsc.scm
cmp "$compiled/gsi/main.scm" gsi/main.scm
for file in "${files[@]}"; do cmp "$compiled/gsc/$file" "gsc/$file"; done
shasum -a 256 ../native-generated-c.patch gsc/_gsc.scm gsi/main.scm > "$output/identity.log"
printf 'NATIVE-GENERATED-C-PATCH-REPLAY-OK original-reverse prepared-forward seven-helper-files\n'
