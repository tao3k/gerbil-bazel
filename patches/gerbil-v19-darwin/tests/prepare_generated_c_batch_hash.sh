#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../../.." && pwd)
original=${1:?owned original bin required}
output=${2:?fresh owned output required}
case "$original:$output" in "$root"/.data/*:"$root"/.data/*) ;; *) exit 2 ;; esac
test ! -e "$output"
mkdir -p "$output"
cp -p "$original/gsc" "$output/gsc"
export PATH="/opt/homebrew/bin:/usr/bin:/bin:$PATH"
sdk=$(/usr/bin/xcrun --sdk macosx --show-sdk-path)
/opt/homebrew/bin/gcc-16 -isysroot "$sdk" -O2 -Wno-deprecated-declarations \
  "$root/patches/gerbil-v19-darwin/tests/gambit-generated-c-batch-sha256.c" \
  -o "$output/gambit-file-sha256"
cmp "$original/gsc" "$output/gsc"
shasum -a 256 "$output/gsc" "$output/gambit-file-sha256"
