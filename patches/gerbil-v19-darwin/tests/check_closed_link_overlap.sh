#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../../.." && pwd)
control=${1:?owned original compiler bin required}
candidate=${2:?owned candidate compiler bin required}
source=${3:?owned real paired Scheme/C source required}
output=${4:?fresh owned receipt required}
home=${5:?owned matching toolchain home required}
case "$control:$candidate:$source:$output:$home" in
  "$root"/.data/*:"$root"/.data/*:"$root"/.data/*:"$root"/.data/*:"$root"/.data/*) ;;
  *) exit 2 ;;
esac
test ! -e "$output"
test -f "$source"
test -f "${source%.scm}.c"
cmp "$home/include/gambit.h" "$candidate/../include/gambit.h"
mkdir -p "$output"
trap 'status=$?; printf "%s\n" "$status" > "$output/exit-status.txt"' EXIT
export GERBIL_HOME="$home" PATH="$candidate:/opt/homebrew/bin:/usr/bin:/bin:$PATH"
export GAMBOPT="~~bin=$candidate,~~lib=$home/lib,~~include=$home/include"
export GAMBIT_DARWIN_CLOSED_LINK_REUSE=1 GAMBIT_GENERATED_C_IN_PROCESS_DIGESTS=1
unset GAMBIT_DARWIN_NATIVE_GENERATED_C GAMBIT_GENERATED_C_PRODUCER_INDEX
cd "$output"
cp "$source" input.scm
for order in c-first scm-first; do
  # Restore identical initial C before each real invocation.
  inputs=(input.c input.scm)
  if test "$order" = scm-first; then inputs=(input.scm input.c); fi
  cp "${source%.scm}.c" input.c
  set +e
  "$control/gsc" -link -flat -o closure.c "${inputs[@]}" > "$order-reference.log" 2>&1
  reference_status=$?
  set -e
  cp input.c reference-input.c
  test ! -f closure.c || cp closure.c reference-link.c
  rm -f closure.c
  cp "${source%.scm}.c" input.c
  set +e
  "$candidate/gsc" -link -flat -closed-c-binding "$order.binding" \
    -o closure.c "${inputs[@]}" > "$order-candidate.log" 2>&1
  candidate_status=$?
  set -e
  test "$candidate_status" = "$reference_status"
  cmp input.c reference-input.c
  if test "$reference_status" = 0; then cmp closure.c reference-link.c; fi
  test ! -e "$order.binding"
  test ! -e "$order.binding.work-"
  if rg -q 'GAMBIT-CLOSED-LINK-SELECTED|GAMBIT-GENERATED-C-(HIT|MISS)' "$order-candidate.log"; then exit 1; fi
  printf 'CLOSED-LINK-OVERLAP-ROUND %s exit=%s original-path-parity\n' "$order" "$candidate_status"
done
printf 'CLOSED-LINK-OVERLAP-OK no-binding no-reuse exact-C-and-link-parity\n'
printf '(define-macro (constant) 17)\n(define result (constant))\n' > macro.scm
"$control/gsc" -link -flat -o macro-reference.c macro.scm > macro-reference.log 2>&1
if "$candidate/gsc" -link -flat -closed-c-binding macro.binding \
  -o macro-candidate.c macro.scm > macro-candidate.log 2>&1; then exit 1; fi
rg -q 'closed link source context is not reusable' macro-candidate.log
test ! -e macro.binding
test ! -e macro.binding.work-
if rg -q 'GAMBIT-CLOSED-LINK-SELECTED' macro-candidate.log; then exit 1; fi
printf 'CLOSED-LINK-MACRO-CONTEXT-OK typed-rejection no-binding failure-cleanup\n'
