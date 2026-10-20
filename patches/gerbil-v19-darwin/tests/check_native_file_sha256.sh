#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../../.." && pwd)
output=${1:?fresh output required}
case "$output" in "$root"/.data/*) ;; *) exit 2 ;; esac
test ! -e "$output"
mkdir -p "$output"
export PATH="/opt/homebrew/bin:/usr/bin:/bin:$PATH"
sdk=$(/usr/bin/xcrun --show-sdk-path)
/opt/homebrew/bin/gcc-16 -O2 -Wall -Wextra -Werror -Wno-deprecated-declarations \
  -isysroot "$sdk" "$root/patches/gerbil-v19-darwin/tests/gambit-file-sha256.c" \
  -o "$output/gambit-file-sha256"
cd "$output"
printf '' > empty
printf 'abc' > abc
printf 'binary\000payload\377\n' > binary
cp binary 'space name'
cp binary 'back\slash'
cp binary $'new\nline'
files=(empty abc binary 'space name' 'back\slash' $'new\nline')
/usr/bin/shasum -a 256 "${files[@]}" > reference.txt
./gambit-file-sha256 "${files[@]}" > native.txt
cmp reference.txt native.txt
test "$(./gambit-file-sha256 --raw abc)" = ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad
ln -s binary symlink
cmp <(./gambit-file-sha256 --raw symlink) <(./gambit-file-sha256 --raw binary)
if ./gambit-file-sha256 missing > missing.out 2> missing.err; then exit 1; fi
test ! -s missing.out
if ./gambit-file-sha256 . > directory.out 2> directory.err; then exit 1; fi
test ! -s directory.out
if ./gambit-file-sha256 > usage.out 2> usage.err; then exit 1; fi
cc1=$(/opt/homebrew/bin/gcc-16 -print-prog-name=cc1)
tools=(/opt/homebrew/bin/gcc-16 "$cc1" /usr/bin/as \
  "$root/.data/d1510-static-reuse-ascent-v1/toolchain/bin/gsc")
/usr/bin/time -p -o reference.time /usr/bin/shasum -a 256 "${tools[@]}" > tools.reference
/usr/bin/time -p -o native.time ./gambit-file-sha256 "${tools[@]}" > tools.native
cmp tools.reference tools.native
printf 'NATIVE-FILE-SHA256-OK\n'
printf 'REFERENCE\n'
cat reference.time
printf 'NATIVE\n'
cat native.time
