#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../../.." && pwd)
bin=${1:?owned native GSC bin required}
source=${2:?owned paired Scheme/C inputs required}
output=${3:?fresh receipt directory required}
home=${4:?owned matching runtime home required}
case "$bin:$source:$output:$home" in "$root"/.data/*:"$root"/.data/*:"$root"/.data/*:"$root"/.data/*) ;; *) exit 2 ;; esac
test ! -e "$output"
cmp "$bin/../include/gambit.h" "$home/include/gambit.h"
mkdir -p "$output/baseline"
trap 'status=$?; printf "%s\n" "$status" > "$output/exit-status.txt"' EXIT
inputs=(); cs=()
for path in "$source"/*.scm; do
  test -f "$path" && test ! -L "$path"
  test -f "${path%.scm}.c" || continue
  name=${path##*/}
  [[ "$name" =~ ^[A-Za-z0-9_.-]+$ ]] || exit 2
  cp "$path" "$output/$name"
  inputs+=("$name"); cs+=("${name%.scm}.c")
done
test "${#inputs[@]}" -gt 1
export GERBIL_HOME="$home"
export GAMBOPT="~~bin=$bin,~~lib=$home/lib,~~include=$home/include"
export PATH="/opt/homebrew/bin:/usr/bin:/bin:$PATH"
unset GAMBIT_DARWIN_CLOSED_LINK_REUSE GAMBIT_DARWIN_NATIVE_GENERATED_C
unset GAMBIT_GENERATED_C_PRODUCER_INDEX GAMBIT_GENERATED_C_BATCH_DIGESTS
unset GAMBIT_GENERATED_C_IN_PROCESS_DIGESTS
cd "$output"
printf '%s\n' "${inputs[@]}" > inputs.txt
shasum -a 256 "${inputs[@]}" > sources-before.sha256
shasum -a 256 "$bin/gsc" > compiler-before.sha256
for name in "${inputs[@]}"; do cp "$name" "baseline/$name"; done
"$bin/gsc" -link -flat -o closure.c "${inputs[@]}" > population.log 2>&1
cp closure.c baseline/link.c
for name in "${cs[@]}"; do cp "$name" "baseline/$name"; done

export MEMBER_CONTROL_MODE=reverse
/usr/bin/time -p -o reverse.time "$bin/gsc" \
  -e "(load \"$root/patches/gerbil-v19-darwin/tests/generated_c_member_independence.scm\")" \
  > reverse.log 2>&1
for name in "${cs[@]}"; do cmp "baseline/$name" "$name"; done
"$bin/gsc" -link -flat -o closure.c "${cs[@]}" > reverse-link.log 2>&1
cmp baseline/link.c closure.c
shasum -a 256 "${inputs[@]}" > sources-after-reverse.sha256
cmp sources-before.sha256 sources-after-reverse.sha256

export MEMBER_CONTROL_MODE=one-change
/usr/bin/time -p -o one-change.time "$bin/gsc" \
  -e "(load \"$root/patches/gerbil-v19-darwin/tests/generated_c_member_independence.scm\")" \
  > one-change.log 2>&1
if cmp -s "baseline/${cs[0]}" "${cs[0]}"; then exit 42; fi
for ((index=1; index<${#cs[@]}; index++)); do cmp "baseline/${cs[index]}" "${cs[index]}"; done
shasum -a 256 "${cs[@]}" > partial-C.sha256
"$bin/gsc" -link -flat -o closure.c "${cs[@]}" > partial-link.log 2>&1
cp closure.c partial-link.c
/usr/bin/time -p -o full-change.time "$bin/gsc" -link -flat \
  -o closure.c "${inputs[@]}" > full-change.log 2>&1
shasum -a 256 "${cs[@]}" > full-C.sha256
cmp partial-C.sha256 full-C.sha256
cmp partial-link.c closure.c
for ((index=1; index<${#cs[@]}; index++)); do cmp "baseline/${cs[index]}" "${cs[index]}"; done

shasum -a 256 "$bin/gsc" > compiler-after.sha256
cmp compiler-before.sha256 compiler-after.sha256
for name in "${inputs[@]}"; do
  cmp "$source/$name" "baseline/$name"
  if test "$name" != "${inputs[0]}"; then cmp "baseline/$name" "$name"; fi
done
for mode in reverse one-change; do
  rg -q "^GENERATED-C-MEMBER-CONTROL-OK $mode modules=${#inputs[@]}$" "$mode.log"
done
printf 'GENERATED-C-MEMBER-INDEPENDENCE-OK modules=%s unchanged=%s C-and-flat-link-byte-parity\n' \
  "${#inputs[@]}" "$((${#inputs[@]}-1))"
printf 'SCOPE component-generation-only no-cache-implementation no-whole-consumer-admission\n'
