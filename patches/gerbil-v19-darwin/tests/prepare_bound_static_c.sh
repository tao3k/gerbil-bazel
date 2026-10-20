#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../../.." && pwd)
original=${1:?owned 0026 driver required}
output=${2:?fresh owned candidate required}
case "$original:$output" in "$root"/.data/*:"$root"/.data/*) ;; *) exit 2 ;; esac
test ! -e "$output"
test -f "$original/gambit-static-object-reuse" && test ! -L "$original/gambit-static-object-reuse"
test "$(shasum -a 256 "$original/gambit-static-object-reuse" | cut -d ' ' -f 1)" = \
  3b6b040aebcc87fcb4b3ab39907f82214c7ea55c6602ac1316128b3d06f38a4b
mkdir -p "$output/source/bin" "$output/bin"
cp "$original/gambit-static-object-reuse" "$output/source/bin/gambit-static-object-reuse.unix"
cp "$original/gambuild-C" "$output/source/bin/gambuild-C.unix.in"
patch -p1 -d "$output/source" < "$root/patches/gerbil-v19-darwin/0027-gambit-darwin-bound-static-c-digest.patch"
cp "$output/source/bin/gambit-static-object-reuse.unix" "$output/bin/gambit-static-object-reuse"
cp "$output/source/bin/gambuild-C.unix.in" "$output/bin/gambuild-C"
cp "$original/gambit-file-sha256" "$output/bin/"
for tool in gsc gxi gerbil; do ln -s "$original/$tool" "$output/bin/$tool"; done
shasum -a 256 "$output/bin/gambit-static-object-reuse" "$output/bin/gambuild-C"
