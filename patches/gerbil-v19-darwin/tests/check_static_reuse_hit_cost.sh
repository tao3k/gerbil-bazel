#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../../.." && pwd)
bin=${1:?owned uninstrumented toolchain bin required}
output=${2:?fresh owned receipt required}
source=${3:?real generated C required}
case "$bin:$output:$source" in "$root"/.data/*:"$root"/.data/*:"$root"/.data/*) ;; *) exit 2 ;; esac
test ! -e "$output"
if test ! -f "$source" || test -L "$source"; then exit 2; fi
if test ! -f "$bin/gambit-static-object-reuse" || test -L "$bin/gambit-static-object-reuse"; then exit 2; fi
test "$(shasum -a 256 "$bin/gambit-static-object-reuse" | cut -d ' ' -f 1)" = \
  08d8ebe59d24a7098561c909c5b8e04c66aff78794d5f68f1cedddf1f2168646
home=$(cd "$bin/.." && pwd)
export GERBIL_HOME="$home"
export GAMBOPT="~~bin=$bin,~~lib=$home/lib,~~include=$home/include"
export PATH="/opt/homebrew/bin:/usr/bin:/bin:$PATH"
unset GCC_EXEC_PREFIX COMPILER_PATH
unset GAMBIT_DARWIN_STATIC_OBJECT_REUSE
mkdir "$output"
cp "$source" "$output/module.c"
cd "$output"
"$bin/gsc" -obj module.c > control.log 2>&1
cp module.o control.o
export GAMBIT_DARWIN_STATIC_OBJECT_REUSE=1
"$bin/gsc" -obj module.c > establish.log 2>&1
rg -q '^GAMBIT-STATIC-OBJECT-MISS$' establish.log
cmp control.o module.o
compiler=$("$bin/gambuild-C" C_COMPILER)
cc1=$("$compiler" -print-prog-name=cc1)
assembler=$("$compiler" -print-prog-name=as)
case "$assembler" in */*) ;; *) assembler=$(command -v "$assembler") ;; esac
apple_as=$(/usr/bin/xcrun --find as)
tools=("$compiler" "$cc1" "$assembler" "$apple_as" "$bin/gambuild-C"
       "$bin/gsc" "$bin/gambit-static-object-reuse" "$bin/gambit-file-sha256")
"$bin/gambit-file-sha256" "${tools[@]}" > tools.before
flags=()
for selector in FLAGS_OPT FLAGS_OBJ DEFS_OBJ; do
  value=$("$bin/gambuild-C" "$selector")
  # The measured toolchain uses plain flag tokens. Do not reinterpret quoted options.
  case "$value" in *\"*|*\'*|*\\*) exit 2 ;; esac
  read -r -a tokens <<< "$value"
  flags+=("${tokens[@]}")
done
for iteration in 1 2 3 4; do
  /usr/bin/time -p -o "$iteration-hit.time" "$bin/gsc" -obj module.c > "$iteration-hit.log" 2>&1
  rg -q '^GAMBIT-STATIC-OBJECT-HIT$' "$iteration-hit.log"
  cmp control.o module.o
  /usr/bin/time -p -o "$iteration-tools.time" "$bin/gambit-file-sha256" \
    "${tools[@]}" > "$iteration-tools.sha256"
  cmp tools.before "$iteration-tools.sha256"
  /usr/bin/time -p -o "$iteration-cpp.time" "$compiler" "${flags[@]}" \
    -I"$home/include" -E -o module.i module.c > "$iteration-cpp.log" 2>&1
  test ! -s "$iteration-cpp.log"
  if test "$iteration" = 1; then cp module.i reference.i; else cmp reference.i module.i; fi
done
"$bin/gambit-file-sha256" "${tools[@]}" > tools.after
cmp tools.before tools.after
test ! -e module.o.gambit-static-lock
shasum -a 256 module.c control.o reference.i > inputs.sha256
printf 'STATIC-HIT-COST-OK four-HITs byte-parity stable-tools stable-cpp\n'
