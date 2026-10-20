#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../../.." && pwd)
control=${1:?owned original compiler bin required}
candidate=${2:?owned role-aware compiler bin required}
source=${3:?owned real paired Scheme/C sources required}
output=${4:?fresh owned receipt required}
home=${5:?owned matching toolchain home required}
case "$control:$candidate:$source:$output:$home" in
  "$root"/.data/*:"$root"/.data/*:"$root"/.data/*:"$root"/.data/*:"$root"/.data/*) ;;
  *) exit 2 ;;
esac
test ! -e "$output"
cmp "$home/include/gambit.h" "$candidate/../include/gambit.h"
mkdir -p "$output/library"
trap 'status=$?; printf "%s\n" "$status" > "$output/exit-status.txt"' EXIT
inputs=(); cs=()
for path in "$source"/*.scm; do
  test -f "${path%.scm}.c" || continue
  name=$(basename "$path")
  cp "$path" "$output/library/$name"
  inputs+=("library/$name"); cs+=("library/${name%.scm}.c")
done
test "${#inputs[@]}" -gt 1
test ! -e "$output/library/role-entry.scm"
printf '(define role-entry-timestamp 1)\n' > "$output/library/role-entry.scm"
inputs+=(library/role-entry.scm); cs+=(library/role-entry.c)
export GERBIL_HOME="$home" PATH="$candidate:/opt/homebrew/bin:/usr/bin:/bin:$PATH"
export GAMBIT_DARWIN_CLOSED_LINK_REUSE=1 GAMBIT_GENERATED_C_IN_PROCESS_DIGESTS=1
unset GAMBIT_DARWIN_NATIVE_GENERATED_C GAMBIT_GENERATED_C_PRODUCER_INDEX
cd "$output"
export GAMBOPT="~~bin=$candidate,~~lib=$home/lib,~~include=$home/include"
for phase in population hit entry-change; do
  if test "$phase" = entry-change; then
    printf '(define role-entry-timestamp 2)\n' > library/role-entry.scm
  fi
  # Both compilers see the same paths and genuine timestamp-bearing entry.
  "$control/gsc" -link -flat -o closure.c "${inputs[@]}" > "$phase-reference.log" 2>&1
  cp closure.c reference-link.c
  /usr/bin/shasum -a 256 "${cs[@]}" > reference-C.sha256
  /usr/bin/time -p -o "$phase.time" "$candidate/gsc" -link -flat \
    -closed-c-binding "$phase.binding" -closed-c-entry library/role-entry.scm \
    -o closure.c "${inputs[@]}" > "$phase.log" 2>&1
  cmp reference-link.c closure.c
  /usr/bin/shasum -a 256 "${cs[@]}" > candidate-C.sha256
  cmp reference-C.sha256 candidate-C.sha256
  export CLOSED_BINDING="$PWD/$phase.binding" CLOSED_BINDING_COUNT=${#inputs[@]}
  "$candidate/gsc" -e "(load \"$root/patches/gerbil-v19-darwin/tests/check_closed_link_manifest.scm\")" > "$phase-manifest.log" 2>&1
  unset CLOSED_BINDING CLOSED_BINDING_COUNT
  printf 'CLOSED-LINK-ROLE-ROUND %s modules=%s\n' "$phase" "${#inputs[@]}"
  cat "$phase.time"
done
test "$(rg -c '^GAMBIT-GENERATED-C-MISS$' population.log)" = 2
test "$(rg -c '^GAMBIT-GENERATED-C-HIT$' hit.log)" = 2
test "$(rg -c '^GAMBIT-GENERATED-C-HIT$' entry-change.log)" = 1
test "$(rg -c '^GAMBIT-GENERATED-C-MISS$' entry-change.log)" = 1
if "$candidate/gsc" -link -flat -closed-c-binding invalid.binding \
  -closed-c-entry not-selected.scm -o closure.c "${inputs[@]}" > invalid.log 2>&1; then exit 1; fi
rg -q 'closed link entry role is not a selected input' invalid.log
test ! -e invalid.binding
test ! -e invalid.binding.work-
"$candidate/gsc" -link -flat -closed-c-binding concurrent-a.binding \
  -closed-c-entry library/role-entry.scm -o concurrent-a.c "${inputs[@]}" > concurrent-a.log 2>&1 &
first=$!
"$candidate/gsc" -link -flat -closed-c-binding concurrent-b.binding \
  -closed-c-entry library/role-entry.scm -o concurrent-b.c "${inputs[@]}" > concurrent-b.log 2>&1 &
second=$!
status=0
wait "$first" || status=1
wait "$second" || status=1
test "$status" = 0
for phase in concurrent-a concurrent-b; do
  # GSC embeds the output basename; compare each candidate with its own name.
  cp "$phase.c" "$phase-candidate.c"
  "$control/gsc" -link -flat -o "$phase.c" "${inputs[@]}" > "$phase-reference.log" 2>&1
  cmp "$phase-candidate.c" "$phase.c"
  export CLOSED_BINDING="$PWD/$phase.binding" CLOSED_BINDING_COUNT=${#inputs[@]}
  "$candidate/gsc" -e "(load \"$root/patches/gerbil-v19-darwin/tests/check_closed_link_manifest.scm\")" > "$phase-manifest.log" 2>&1
  unset CLOSED_BINDING CLOSED_BINDING_COUNT
  test ! -e "$phase.binding.work-"
done
printf 'CLOSED-LINK-ENTRY-ROLE-OK stable-group-HIT entry-change-MISS full-C-and-link-parity invalid-role-cleanup\n'
printf 'CLOSED-LINK-ENTRY-CONCURRENCY-OK two-independent-links exact-link-and-manifest-parity\n'
