#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../../.." && pwd)
original=${1:?owned frozen ASCENT workspace required}
native=${2:?owned matching native GSC build required}
output=${3:?fresh owned workspace required}
case "$original:$native:$output" in "$root"/.data/*:"$root"/.data/*:"$root"/.data/*) ;; *) exit 2 ;; esac
test ! -e "$output"
test "$(git -C "$original/project" rev-parse HEAD)" = 21e3638687d42ecfc36acebb28991987435ebc60
test -z "$(git -C "$original/project" status --porcelain --untracked-files=no)"
if test -n "${5:-}"; then
  python3 "$root/patches/gerbil-v19-darwin/tests/native_generated_c_profile.py" \
    --driver "$native/bin" --runtime "$original/toolchain" --lock "$5"
fi
cmp "$original/toolchain/include/gambit.h" "$native/include/gambit.h"
mkdir "$output"
for name in project toolchain dependencies; do
  /bin/cp -cR "$original/$name" "$output/$name"
done
# Only the fresh COW copy is cleared; no hard links or active caches are used.
cache="$output/project/.cache/ascent"
test ! -L "$cache"
rm -rf "$cache"
test ! -L "$output/toolchain/bin/gsc"
cp -p "$native/bin/gsc" "$output/toolchain/bin/gsc"
cp -p "$native/bin/gambit-file-sha256" "$output/toolchain/bin/gambit-file-sha256"
cp "$original/toolchain-dynamic-references.json" "$output/toolchain-dynamic-references.json"
cp "$original/dependency-dynamic-references.json" "$output/dependency-dynamic-references.json"
python3 "$root/patches/gerbil-v19-darwin/tests/experiment_framework/ascent_profile.py" \
  --isolated "$output/toolchain" --receipt "$output/toolchain-dynamic-references.json" --verify
python3 "$root/patches/gerbil-v19-darwin/tests/experiment_framework/ascent_profile.py" \
  --isolated "$output/dependencies" --receipt "$output/dependency-dynamic-references.json" --verify
if test -n "${4:-}"; then
  python3 "$root/patches/gerbil-v19-darwin/tests/experiment_framework/ascent_profile.py" \
    --isolated "$output/toolchain" --receipt "$output/toolchain-dynamic-references.json" \
    --overlay-library "$4" --module std/make
fi
printf 'ASCENT-NATIVE-GSC-ISOLATION-READY\n'
