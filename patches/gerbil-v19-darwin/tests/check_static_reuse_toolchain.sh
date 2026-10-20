#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../../.." && pwd)
original=${1:?isolated driver bin required}
output=${2:?fresh output required}
home=${3:-"$root/.data/d1391-runtime-object-source/build"}
case "$original:$output" in "$root"/.data/*:"$root"/.data/*) ;; *) exit 2 ;; esac
case "$home" in "$root"/.data/*) ;; *) exit 2 ;; esac
if test ! -f "$home/include/gambit.h" || test -L "$home/include/gambit.h"; then exit 2; fi
test ! -e "$output"
mkdir -p "$output/bin" "$output/work"
bin="$output/bin"
cp "$original/gambit-static-object-reuse" "$original/gambit-file-sha256" "$bin/"
cp /opt/homebrew/bin/gcc-16 "$bin/compiler"
chmod u+w "$bin/compiler"
sed "s|/opt/homebrew/bin/gcc-16|$bin/compiler|g" "$original/gambuild-C" > "$bin/gambuild-C"
chmod +x "$bin/gambuild-C"
for tool in gsc gxi gerbil; do ln -s "$original/$tool" "$bin/$tool"; done
export PATH="$bin:/opt/homebrew/bin:/usr/bin:/bin:$PATH"
export GCC_EXEC_PREFIX="$(dirname "$(/opt/homebrew/bin/gcc-16 -print-prog-name=cc1)")/"
shasum -a 256 "$home/include/gambit.h" "$original/gsc" > "$output/selected-toolchain.sha256"
export GERBIL_HOME="$home"
export GAMBOPT="~~bin=$bin,~~lib=$home/lib,~~include=$home/include"
export GAMBIT_DARWIN_STATIC_OBJECT_REUSE=1
cd "$output/work"
printf 'int toolchain_probe(void) { return 17; }\n' > probe.c
"$bin/gsc" -obj probe.c > cold.log 2>&1
"$bin/gsc" -obj probe.c > establish.log 2>&1
"$bin/gsc" -obj probe.c > hit.log 2>&1
rg -q '^GAMBIT-STATIC-OBJECT-HIT$' hit.log
cp probe.o original.o
# Alter only the private real GCC executable, never the installed compiler.
printf '\nprivate-compiler-content-invalidation\n' >> "$bin/compiler"
"$bin/gsc" -obj probe.c > compiler-change.log 2>&1
rg -q '^GAMBIT-STATIC-OBJECT-MISS$' compiler-change.log
cmp original.o probe.o
"$bin/gsc" -obj probe.c > compiler-repeat.log 2>&1
rg -q '^GAMBIT-STATIC-OBJECT-HIT$' compiler-repeat.log
export STATIC_REUSE_AS_LOG="$PWD/assembler-invocations"
printf '%s\n' '#!/bin/sh' \
  'printf "ASM-EXEC\n" >> "$STATIC_REUSE_AS_LOG"' \
  'exec /usr/bin/as "$@"' > "$bin/as"
chmod +x "$bin/as"
"$bin/gsc" -obj probe.c > assembler-establish.log 2>&1
rg -q '^GAMBIT-STATIC-OBJECT-MISS$' assembler-establish.log
rg -q '^ASM-EXEC$' "$STATIC_REUSE_AS_LOG"
cmp original.o probe.o
cp "$STATIC_REUSE_AS_LOG" assembler-before-hit
"$bin/gsc" -obj probe.c > assembler-hit.log 2>&1
rg -q '^GAMBIT-STATIC-OBJECT-HIT$' assembler-hit.log
cmp assembler-before-hit "$STATIC_REUSE_AS_LOG"
printf '\n# Private assembler entry content change.\n' >> "$bin/as"
"$bin/gsc" -obj probe.c > assembler-change.log 2>&1
rg -q '^GAMBIT-STATIC-OBJECT-MISS$' assembler-change.log
cmp original.o probe.o
if cmp -s assembler-before-hit "$STATIC_REUSE_AS_LOG"; then exit 1; fi
"$bin/gsc" -obj probe.c > assembler-repeat.log 2>&1
rg -q '^GAMBIT-STATIC-OBJECT-HIT$' assembler-repeat.log
printf '\nprivate-native-digest-content-invalidation\n' >> "$bin/gambit-file-sha256"
"$bin/gsc" -obj probe.c > digest-change.log 2>&1
rg -q '^GAMBIT-STATIC-OBJECT-MISS$' digest-change.log
cmp original.o probe.o
cp probe.o.gambit-static-proof before-digest-failure.proof
mv "$bin/gambit-file-sha256" "$bin/gambit-file-sha256.unavailable"
if "$bin/gsc" -obj probe.c > digest-unavailable.log 2>&1; then exit 1; fi
cmp original.o probe.o
cmp before-digest-failure.proof probe.o.gambit-static-proof
mv "$bin/gambit-file-sha256.unavailable" "$bin/gambit-file-sha256"
# The platform fallback must not acquire a lock or modify existing proof state.
(
  uname() { printf 'Linux\n'; }
  . "$bin/gambit-static-object-reuse"
  BUILD_OBJ_CMD='printf "ORIGINAL-PLATFORM-COMMAND\\n"'
  BUILD_OBJ_OUTPUT_FILENAME_PARAM="$PWD/platform.o"
  mkdir "$BUILD_OBJ_OUTPUT_FILENAME_PARAM.gambit-static-lock"
  printf 'existing-proof\n' > "$BUILD_OBJ_OUTPUT_FILENAME_PARAM.gambit-static-proof"
  gambuild_obj_with_static_reuse > platform.log
  test "$(cat platform.log)" = ORIGINAL-PLATFORM-COMMAND
  test "$(cat "$BUILD_OBJ_OUTPUT_FILENAME_PARAM.gambit-static-proof")" = existing-proof
  rmdir "$BUILD_OBJ_OUTPUT_FILENAME_PARAM.gambit-static-lock"
)
test ! -d probe.o.gambit-static-lock
printf 'STATIC-OBJECT-TOOLCHAIN-OK 5\n'
