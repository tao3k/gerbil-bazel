#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../../.." && pwd)
home=${1:?owned matching home required}
recorder=${2:?owned compiled native recorder required}
output=${3:?fresh owned diagnostic directory required}
case "$home:$recorder:$output" in "$root"/.data/*:"$root"/.data/*:"$root"/.data/*) ;; *) exit 2 ;; esac
test ! -e "$output"
if test ! -f "$recorder" || test -L "$recorder"; then exit 2; fi
for tool in compiler gsc gambuild-C gambit-static-object-reuse gambit-file-sha256; do
  if test ! -f "$home/bin/$tool" || test -L "$home/bin/$tool"; then exit 2; fi
done
mkdir -p "$output/bin"
for tool in gsc compiler gcc; do
  cp "$recorder" "$output/bin/$tool"
  chmod +x "$output/bin/$tool"
  target="$home/bin/$tool"
  if test "$tool" = gcc; then target="$home/bin/compiler"; fi
  printf '%s\n' "$target" > "$output/bin/$tool.target"
done
cp "$home/bin/gambit-static-object-reuse" "$home/bin/gambit-file-sha256" "$output/bin/"
sed "s|$home/bin/compiler|$output/bin/compiler|g" "$home/bin/gambuild-C" > "$output/bin/gambuild-C"
chmod +x "$output/bin/gambuild-C"
shasum -a 256 "$home/bin/gsc" "$home/bin/compiler" "$home/bin/gambuild-C" \
  "$home/bin/gambit-static-object-reuse" "$home/bin/gambit-file-sha256" > "$output/delegates-before.sha256"
printf 'NATIVE-PHASE-DRIVER-READY diagnostic-only unchanged-native-delegates\n'
