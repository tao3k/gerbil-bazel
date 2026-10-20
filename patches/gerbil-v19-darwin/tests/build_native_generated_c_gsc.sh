#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../../.." && pwd)
source=${1:?owned Gambit source required}
runtime=${2:?owned matching runtime required}
hashbin=${3:?owned experimental hash bin required}
output=${4:?fresh owned output required}
case "$source:$runtime:$hashbin:$output" in "$root"/.data/*:"$root"/.data/*:"$root"/.data/*:"$root"/.data/*) ;; *) exit 2 ;; esac
prepare_options=()
case "${5:-external}" in
  external) ;;
  native-digests) prepare_options+=(--native-digests) ;;
  *) exit 2 ;;
esac
case "${6:-all-producers}" in
  all-producers) ;;
  planned-producers) prepare_options+=(--planned-producers) ;;
  *) exit 2 ;;
esac
case "${7:-original-reader}" in
  original-reader) ;;
  snapshot-reader) prepare_options+=(--snapshot-reader) ;;
  *) exit 2 ;;
esac
case "${8:-existing-hooks}" in
  existing-hooks) ;;
  closed-link-only) prepare_options+=(--closed-link-only) ;;
  *) exit 2 ;;
esac
case "${9:-per-request-tools}" in
  per-request-tools) ;;
  member-tools) prepare_options+=(--member-tools) ;;
  *) exit 2 ;;
esac
python3 "$root/patches/gerbil-v19-darwin/tests/prepare_native_generated_c_gsc.py" --source "$source" --output "$output" "${prepare_options[@]}"
mkdir "$output/bin" "$output/include"
cp -p "$runtime/include/gambit.h" "$output/include/gambit.h"
cp -p "$source/include/config.h" "$output/include/config.h"
export PATH="/opt/homebrew/bin:/usr/bin:/bin:$PATH"
export GAMBOPT="~~bin=$runtime/bin,~~lib=$runtime/lib,~~include=$runtime/include"
sdk=$(/usr/bin/xcrun --sdk macosx --show-sdk-path)
cd "$output/gsc"
prelude="(##namespace(\"c#\"))(##include\"$source/lib/header.scm\")"
"$runtime/bin/gsc" -f -prelude "$prelude" -c _gsc.scm > "$output/generate.log" 2>&1
"$runtime/bin/gsc" -f -prelude "$prelude" -link -l "$source/gsc/_gambitgsc" -o _gsc_.c -preload _gsc.c > "$output/link-metadata.log" 2>&1
ln -s "$source/gsc/_gambitgsc.c" _gambitgsc.c
make --no-print-directory -f "$source/gsc/makefile" -j2 \
  -o _gsc.c -o _gsc_.c -o _gambitgsc.c \
  C_COMPILER="/opt/homebrew/bin/gcc-16 -ftrack-macro-expansion=0 -isysroot \"$sdk\"" \
  DEFS_OBJ=-DHAVE_CONFIG_H GAMBITDIR_INCLUDE="$output/include" \
  _gsc.o _gsc_.o > "$output/objects.log" 2>&1
/opt/homebrew/bin/gcc-16 -isysroot "$sdk" -o "$output/bin/gsc" _gsc.o _gsc_.o \
  "$runtime/lib/libgambitgsc.a" "$runtime/lib/libgambit.a" > "$output/link-native.log" 2>&1
cp -p "$hashbin/gambit-file-sha256" "$output/bin/gambit-file-sha256"
shasum -a 256 "$output/bin/gsc" "$output/bin/gambit-file-sha256" > "$output/identity.log"
shasum -a 256 "$runtime/include/gambit.h" "$output/include/gambit.h" \
  "$runtime/lib/libgambit.a" "$runtime/lib/libgambitgsc.a" "$output/include/config.h" > "$output/abi-identity.log"
printf 'NATIVE-GENERATED-C-GSC-BUILD-OK\n'
