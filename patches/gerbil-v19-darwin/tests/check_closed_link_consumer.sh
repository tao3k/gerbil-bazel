#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../../.." && pwd)
control=${1:?owned original compiler bin required}
candidate=${2:?owned closed-link compiler bin required}
source=${3:?owned real paired Scheme/C source required}
output=${4:?fresh owned receipt required}
home=${5:?owned matching toolchain home required}
mode=${6:-group}
case "$mode" in group|member|member-proof-only|member-tools-only) ;; *) exit 2 ;; esac
case "$control:$candidate:$source:$output:$home" in
  "$root"/.data/*:"$root"/.data/*:"$root"/.data/*:"$root"/.data/*:"$root"/.data/*) ;;
  *) exit 2 ;;
esac
test ! -e "$output"
cmp "$home/include/gambit.h" "$candidate/../include/gambit.h"
mkdir -p "$output/a" "$output/b"
trap 'status=$?; printf "%s\n" "$status" > "$output/exit-status.txt"' EXIT
inputs=(); cs=(); index=0
for path in "$source"/*.scm; do
  test -f "${path%.scm}.c" || continue
  test ! -L "$path"
  index=$((index+1))
  directory=a
  if test "$((index%2))" = 0; then directory=b; fi
  name=$(basename "$path")
  cp "$path" "$output/$directory/$name"
  inputs+=("$directory/$name")
  cs+=("$directory/${name%.scm}.c")
done
test "${#inputs[@]}" -gt 1
export GERBIL_HOME="$home"
export PATH="$candidate:/opt/homebrew/bin:/usr/bin:/bin:$PATH"
unset GAMBIT_DARWIN_NATIVE_GENERATED_C GAMBIT_GENERATED_C_PRODUCER_INDEX
unset GAMBIT_DARWIN_CLOSED_LINK_REUSE GAMBIT_GENERATED_C_IN_PROCESS_DIGESTS
unset GAMBIT_DARWIN_CLOSED_LINK_MEMBER_PROOF GAMBIT_DARWIN_CLOSED_LINK_MEMBER_TOOLS_BATCH
if test "$mode" = member; then
  export GAMBIT_DARWIN_CLOSED_LINK_MEMBER_PROOF=1 GAMBIT_DARWIN_CLOSED_LINK_MEMBER_TOOLS_BATCH=1
elif test "$mode" = member-proof-only; then
  export GAMBIT_DARWIN_CLOSED_LINK_MEMBER_PROOF=1
elif test "$mode" = member-tools-only; then
  export GAMBIT_DARWIN_CLOSED_LINK_MEMBER_TOOLS_BATCH=1
fi
cd "$output"
printf 'mode=%s\n' "$mode" > mode.txt
export GAMBOPT="~~bin=$control,~~lib=$home/lib,~~include=$home/include"
"$control/gsc" -link -flat -o closure.c "${inputs[@]}" > reference.log 2>&1
cp closure.c reference-link.c
/usr/bin/shasum -a 256 "${cs[@]}" > reference-C.sha256
export GAMBOPT="~~bin=$candidate,~~lib=$home/lib,~~include=$home/include"
"$candidate/gsc" -link -flat -closed-c-binding off.binding -o closure.c "${inputs[@]}" > off.log 2>&1
test ! -e off.binding
cmp reference-link.c closure.c
export GAMBIT_DARWIN_CLOSED_LINK_REUSE=1 GAMBIT_GENERATED_C_IN_PROCESS_DIGESTS=1
for phase in population hit; do
  /usr/bin/time -p -o "$phase.time" "$candidate/gsc" -link -flat \
    -closed-c-binding "$phase.binding" -o closure.c "${inputs[@]}" > "$phase.log" 2>&1
  cmp reference-link.c closure.c
  /usr/bin/shasum -a 256 "${cs[@]}" > candidate-C.sha256
  cmp reference-C.sha256 candidate-C.sha256
  rg -q "^GAMBIT-CLOSED-LINK-SELECTED ${#inputs[@]}$" "$phase.log"
  export CLOSED_BINDING="$PWD/$phase.binding" CLOSED_BINDING_COUNT=${#inputs[@]}
  "$candidate/gsc" -e "(load \"$root/patches/gerbil-v19-darwin/tests/check_closed_link_manifest.scm\")" > "$phase-manifest.log" 2>&1
  unset CLOSED_BINDING CLOSED_BINDING_COUNT
  printf 'CLOSED-LINK-ROUND %s modules=%s\n' "$phase" "${#inputs[@]}"
  cat "$phase.time"
done
# Inputs deliberately alternate directories. Ordered contiguous groups cannot
# merge them by moving a later source ahead of an earlier source.
test "$(rg -c '^GAMBIT-GENERATED-C-MISS$' population.log)" = "${#inputs[@]}"
test "$(rg -c '^GAMBIT-GENERATED-C-HIT$' hit.log)" = "${#inputs[@]}"
cmp population.binding hit.binding
if test "$mode" = member; then
  test "$(rg --files --hidden -g '*.gambit-member-proof' a b | wc -l | tr -d ' ')" = "${#inputs[@]}"
else
  if rg --files --hidden -g '*.gambit-member-proof' a b | rg -q .; then exit 42; fi
fi
# Unsupported transformations remain ordinary GSC work, without publishing a
# binding. Do not silently call the narrow closure adapter with extra options.
"$candidate/gsc" -link -flat -debug-source -closed-c-binding unsupported.binding \
  -o closure.c "${inputs[@]}" > unsupported.log 2>&1
test ! -e unsupported.binding
test ! -e unsupported.binding.work
mixed=(); index=0
for input in "${inputs[@]}"; do
  index=$((index+1))
  if test "$((index%2))" = 0; then
    mixed+=(-nopreload "$input")
  else
    mixed+=(-preload "${input%.scm}.c")
  fi
done
"$control/gsc" -link -flat -o mixed.c "${mixed[@]}" > mixed-reference.log 2>&1
cp mixed.c mixed-reference.c
"$candidate/gsc" -link -flat -closed-c-binding mixed.binding \
  -o mixed.c "${mixed[@]}" > mixed-candidate.log 2>&1
cmp mixed-reference.c mixed.c
export CLOSED_BINDING="$PWD/mixed.binding" CLOSED_BINDING_COUNT=${#inputs[@]}
"$candidate/gsc" -e "(load \"$root/patches/gerbil-v19-darwin/tests/check_closed_link_manifest.scm\")" > mixed-manifest.log 2>&1
unset CLOSED_BINDING CLOSED_BINDING_COUNT
printf 'CLOSED-LINK-CONSUMER-OK mixed-directories order C-parity link-parity default-off unsupported\n'
