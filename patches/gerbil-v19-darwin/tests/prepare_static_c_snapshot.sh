#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../../.." && pwd)
original=${1:?owned frozen driver bin required}
output=${2:?fresh owned candidate required}
case "$original:$output" in "$root"/.data/*:"$root"/.data/*) ;; *) exit 2 ;; esac
test ! -e "$output"
test -f "$original/gambit-static-object-reuse" && test ! -L "$original/gambit-static-object-reuse"
test "$(shasum -a 256 "$original/gambit-static-object-reuse" | cut -d ' ' -f 1)" = \
  08d8ebe59d24a7098561c909c5b8e04c66aff78794d5f68f1cedddf1f2168646
mkdir -p "$output/source/bin" "$output/bin"
cp "$original/gambit-static-object-reuse" "$output/source/bin/gambit-static-object-reuse.unix"
patch -p1 -d "$output/source" < "$root/patches/gerbil-v19-darwin/0026-gambit-darwin-static-c-snapshot-input.patch"
cp "$output/source/bin/gambit-static-object-reuse.unix" "$output/bin/gambit-static-object-reuse"
cp "$original/gambuild-C" "$original/gambit-file-sha256" "$output/bin/"
for tool in gsc gxi gerbil; do ln -s "$original/$tool" "$output/bin/$tool"; done
shasum -a 256 "$output/bin/gambit-static-object-reuse"
