#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../../.." && pwd)
bin=${1:?selected driver bin required}
output=${2:?fresh owned output required}
compiler=${3:?genuine GNU GCC executable required}
case "$output" in "$root"/.data/*) ;; *) exit 2 ;; esac
test ! -e "$output"
mkdir -p "$output"
cd "$output"
"$compiler" --version > compiler.txt
macros=$("$compiler" -dM -E -x c /dev/null)
grep -q __GNUC__ <<< "$macros"
if grep -q __clang__ <<< "$macros"; then exit 2; fi
. "$bin/gambit-static-object-reuse"
C_COMPILER="$compiler"
BUILD_OBJ_CC_OPTIONS_PARAM= FLAGS_OBJ= FLAGS_OPT= DEFS_OBJ=
BUILD_OBJ='original compiler command'
names=($'embedded\nnewline.c' $'embedded\rcarriage.c' $'embedded\r\npair.c' $'directory\n/probe.c')
index=0
for name in "${names[@]}"; do
  index=$((index + 1))
  case "$name" in */*) mkdir -p "${name%/*}" ;; esac
  printf 'int snapshot_path_probe(void) { return 17; }\n' > "$name"
  object="${name%.c}.o"
  "$compiler" -c "$name" -o "$object" > "$index-control.log" 2>&1
  cp "$object" "$index-control.o"
  # Existing output enters the eligible warm path; it must still fall back.
  BUILD_OBJ_INPUT_FILENAMES_PARAM="$name"
  BUILD_OBJ_OUTPUT_FILENAME_PARAM="$object"
  printf -v BUILD_OBJ_CMD '%q -c %q -o %q' "$compiler" "$name" "$object"
  gambuild_obj_with_static_reuse > "$index-candidate.log" 2>&1
  cmp "$index-control.o" "$object"
  cmp "$index-control.log" "$index-candidate.log"
  test ! -e "$object.gambit-static-proof"
  test ! -e "$object.gambit-static-lock"
  printf 'int snapshot_path_probe(void) { invalid C syntax; }\n' > "$name"
  set +e
  "$compiler" -c "$name" -o "$object" > "$index-failure-control.log" 2>&1
  control_status=$?
  gambuild_obj_with_static_reuse > "$index-failure-candidate.log" 2>&1
  candidate_status=$?
  set -e
  test "$control_status" -ne 0
  test "$candidate_status" -eq "$control_status"
  cmp "$index-failure-control.log" "$index-failure-candidate.log"
  cmp "$index-control.o" "$object"
  test ! -e "$object.gambit-static-lock"
done
printf 'STATIC-SNAPSHOT-PATH-FALLBACK-OK 8\n'
