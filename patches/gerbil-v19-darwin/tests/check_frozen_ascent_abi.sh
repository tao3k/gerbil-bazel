#!/usr/bin/env bash
# Qualify the frozen helper with ASCENT's actual Multiple-VM compiler/header pair.
set -euo pipefail
root=$(cd "$(dirname "$0")/../../.." && pwd)
workspace=${1:?owned frozen ASCENT workspace required}
output=${2:?fresh owned contract receipt required}
case "$workspace:$output" in "$root"/.data/*:"$root"/.data/*) ;; *) exit 2 ;; esac
test ! -e "$output"
home="$workspace/toolchain"
original="$home/bin"
source="$workspace/project/.cache/ascent/native-library/lib/static/gerbil-ascent__core__dependency-graph.c"
if test ! -f "$source" || test -L "$source"; then exit 2; fi
if test ! -f "$home/include/gambit.h" || test -L "$home/include/gambit.h"; then exit 2; fi
rg -q '^#define ___MULTIPLE_VMS$' "$home/include/gambit.h"
test "$(shasum -a 256 "$home/include/gambit.h" | cut -d ' ' -f 1)" = \
  8257ff05aadb634e2ef2532f7e1a21608a828c4adae35cf88276b78e7efff1e5
test "$(shasum -a 256 "$original/gambit-static-object-reuse" | cut -d ' ' -f 1)" = \
  3b6b040aebcc87fcb4b3ab39907f82214c7ea55c6602ac1316128b3d06f38a4b
test "$(shasum -a 256 "$original/gambit-file-sha256" | cut -d ' ' -f 1)" = \
  e0124f9b69561d6fc34b148aa57e1573aebb7f3adc0ef4470b657f895156f2df
test "$(shasum -a 256 "$original/gsc" | cut -d ' ' -f 1)" = \
  dd32a1694062deb4175641bbfe51c23f2d9d9efa5770fe5b1a2f75d68557984e
cmp "$original/compiler" /opt/homebrew/bin/gcc-16
mkdir -p "$output/bin"
trap 'status=$?; printf "%s\n" "$status" > "$output/exit-status.txt"' EXIT
bin="$output/bin"
cp "$original/gambit-static-object-reuse" "$original/gambit-file-sha256" "$bin/"
# Existing mutation controls substitute this spelling to create private compilers.
# Only the owned configured driver is normalized; all ABI/options stay unchanged.
sed "s|$original/compiler|/opt/homebrew/bin/gcc-16|g" "$original/gambuild-C" > "$bin/gambuild-C"
chmod +x "$bin/gambuild-C"
for tool in gsc gxi gerbil; do ln -s "$original/$tool" "$bin/$tool"; done
export PATH="/opt/homebrew/bin:/usr/bin:/bin:$PATH"
unset NIX_CFLAGS_COMPILE NIX_LDFLAGS CPATH C_INCLUDE_PATH CPLUS_INCLUDE_PATH
unset CFLAGS CPPFLAGS LDFLAGS SDKROOT DEVELOPER_DIR GCC_EXEC_PREFIX COMPILER_PATH
unset GAMBIT_DARWIN_OBJECT_PREPARE_DIRECTORY GAMBIT_DARWIN_NATIVE_OBJECT_BATCH
unset GAMBIT_DARWIN_NATIVE_OBJECT_CAPTURE GAMBIT_DARWIN_NATIVE_OBJECT_CHECK
unset GAMBIT_DARWIN_BOUND_SINGLE_PASS GAMBIT_DARWIN_STATIC_EXPECTED_SOURCE_SHA
shasum -a 256 "$original/gambuild-C" "$original/gambit-static-object-reuse" \
  "$original/gambit-file-sha256" "$original/gsc" "$home/include/gambit.h" \
  /opt/homebrew/bin/gcc-16 > "$output/original-before.sha256"
tests="$root/patches/gerbil-v19-darwin/tests"
for control in object identity safety toolchain; do
  script=check_static_reuse_${control}.sh
  if test "$control" = object; then script=check_static_object_reuse.sh; fi
  arguments=("$bin" "$output/$control" "$home")
  if test "$control" = object; then arguments+=("$source"); fi
  bash "$tests/$script" "${arguments[@]}" > "$output/$control.log" 2>&1
  cat "$output/$control.log"
done
for phase in preprocess compile; do
  bash "$tests/check_static_source_aba.sh" "$bin" "$output/aba-existing-$phase" \
    "$home" protected existing "$phase" > "$output/aba-existing-$phase.log" 2>&1
  cat "$output/aba-existing-$phase.log"
done
shasum -a 256 "$original/gambuild-C" "$original/gambit-static-object-reuse" \
  "$original/gambit-file-sha256" "$original/gsc" "$home/include/gambit.h" \
  /opt/homebrew/bin/gcc-16 > "$output/original-after.sha256"
cmp "$output/original-before.sha256" "$output/original-after.sha256"
printf 'FROZEN-ASCENT-ABI-OK 22-contracts two-existing-object-ABA-controls Multiple-VM original-toolchain-unchanged\n'
