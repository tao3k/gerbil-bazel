#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../../.." && pwd)
stack="$root/patches/gerbil-v19-darwin"
source=${1:?owned previously composed source fixture required}
driver=${2:?frozen measured v4 driver bin required}
output=${3:?fresh owned output required}
runtime=${4:?frozen measured runtime directory required}
evidence=${5:-$root}
bundle=${6:-v4}
gsc=${7:-}
case "$bundle" in
  v4) lock=d1510-mcp-v4-patch-lock.json; series=mcp-v4-driver.series; count=5 ;;
  snapshot) lock=d1510-static-c-snapshot-patch-lock.json; series=static-c-snapshot-candidate.series; count=6
    test -n "$gsc" || { printf 'PATCH-REPLAY-DENY snapshot requires selected GSC\n' >&2; exit 2; } ;;
  *) printf 'PATCH-REPLAY-DENY unknown bundle\n' >&2; exit 2 ;;
esac
case "$source:$driver:$output:$runtime" in "$root"/.data/*:"$root"/.data/*:"$root"/.data/*:"$root"/.data/*) ;; *) exit 2 ;; esac
test ! -e "$output"
gsc_args=()
if test -n "$gsc"; then gsc_args=(--gsc "$gsc"); fi
if test "$bundle" = snapshot; then
  gsc_args+=(--lock-sha256 a6c612404a9b9c6fde63e198ae25d590b814a57c5d628e6fcce203e0fdbe45a2)
fi
python3 "$stack/tests/experiment_framework/patch_lock.py" \
  "$stack/receipts/$lock" \
  --driver "$driver" --runtime "$runtime" --evidence-root "$evidence" --performance "${gsc_args[@]}"
mkdir -p "$output/source/bin"
files=(gambuild-C.unix.in makefile.in gambit-native-object-cache.unix gambit-static-object-reuse.unix gambit-file-sha256.c)
for file in "${files[@]}"; do
  test -f "$source/bin/$file" && test ! -L "$source/bin/$file"
  cp "$source/bin/$file" "$output/source/bin/$file"
done
patches=()
while IFS= read -r patch; do patches+=("$stack/$patch"); done < "$stack/$series"
test "${#patches[@]}" = "$count"
cd "$output/source"
git init -q
for ((index=${#patches[@]}-1; index>=0; index--)); do
  git apply --reverse --check "${patches[index]}"
  git apply --reverse "${patches[index]}"
done
for file in gambit-native-object-cache.unix gambit-static-object-reuse.unix gambit-file-sha256.c; do
  test ! -e "bin/$file"
done
for patch in "${patches[@]}"; do
  git apply --check "$patch"
  git apply "$patch"
done
for file in "${files[@]}"; do cmp "$source/bin/$file" "bin/$file"; done
cmp bin/gambit-static-object-reuse.unix "$driver/gambit-static-object-reuse"
cmp bin/gambit-file-sha256.c "$stack/tests/gambit-file-sha256.c"
(
  cd "$stack"
  while IFS= read -r patch; do shasum -a 256 "$patch"; done < "$series"
) > "$output/identity.log"
shasum -a 256 bin/gambit-static-object-reuse.unix bin/gambit-file-sha256.c >> "$output/identity.log"
if test "$bundle" = v4; then
  printf 'MCP-V4-PATCH-REPLAY-OK five-patches source-parity measured-helper-parity\n'
else
  printf 'STATIC-SNAPSHOT-PATCH-REPLAY-OK six-patches source-parity measured-helper-parity\n'
fi
