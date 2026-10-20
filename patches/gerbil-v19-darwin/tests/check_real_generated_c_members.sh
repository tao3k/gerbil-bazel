#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../../.." && pwd)
bin=${1:?owned native GSC bin required}
source=${2:?owned paired Scheme/C inputs required}
output=${3:?fresh receipt required}
home=${4:?owned matching runtime required}
tools_mode=${5:-per-member}
api_mode=${6:-interpreted}
case "$tools_mode" in per-member|batch) ;; *) exit 2 ;; esac
case "$api_mode" in interpreted|compiled) ;; *) exit 2 ;; esac
case "$bin:$source:$output:$home" in "$root"/.data/*:"$root"/.data/*:"$root"/.data/*:"$root"/.data/*) ;; *) exit 2 ;; esac
test ! -e "$output"
cmp "$bin/../include/gambit.h" "$home/include/gambit.h"
mkdir -p "$output/baseline" "$output/published"
trap 'status=$?; printf "%s\n" "$status" > "$output/exit-status.txt"' EXIT
inputs=(); cs=()
for path in "$source"/*.scm; do
  test -f "$path" && test ! -L "$path"
  test -f "${path%.scm}.c" || continue
  name=${path##*/}
  [[ "$name" =~ ^[A-Za-z0-9_.-]+$ ]] || exit 2
  cp "$path" "$output/$name"
  cp "$path" "$output/baseline/$name"
  inputs+=("$name"); cs+=("${name%.scm}.c")
done
test "${#inputs[@]}" -gt 1
export GERBIL_HOME="$home" PATH="/opt/homebrew/bin:/usr/bin:/bin:$PATH"
export GAMBOPT="~~bin=$bin,~~lib=$home/lib,~~include=$home/include"
export GENERATION_BIN="$bin" GENERATION_FIXTURE="$output"
export GENERATION_IMPLEMENTATION="$root/patches/gerbil-v19-darwin/tests/gambit-generated-c-members.scm"
export GENERATION_CONTRACT="$root/patches/gerbil-v19-darwin/tests/generated_c_member_benchmark.scm"
export GAMBIT_DARWIN_CLOSED_LINK_MEMBER_PROOF=1 GAMBIT_GENERATED_C_IN_PROCESS_DIGESTS=1
unset GAMBIT_DARWIN_CLOSED_LINK_MEMBER_TOOLS_BATCH
if test "$tools_mode" = batch; then export GAMBIT_DARWIN_CLOSED_LINK_MEMBER_TOOLS_BATCH=1; fi
unset GAMBIT_DARWIN_CLOSED_LINK_REUSE GAMBIT_DARWIN_NATIVE_GENERATED_C GAMBIT_GENERATED_C_PRODUCER_INDEX
api_args=(-e '(load (getenv "GENERATION_IMPLEMENTATION"))')
if test "$api_mode" = compiled; then
  cmp "$bin/../gsc/gambit-generated-c-members.scm" "$GENERATION_IMPLEMENTATION"
  api_args=(-e '(define reuse-generated-c-members! c#reuse-generated-c-members!)')
fi
cd "$output"
printf 'tools=%s api=%s\n' "$tools_mode" "$api_mode" > mode.txt
printf '%s\n' "${inputs[@]}" > inputs.txt
for phase in group-populate member-populate group-hit member-hit group-change member-change; do
  /usr/bin/time -p -o "$phase.time" gtimeout --signal=TERM --kill-after=1 30s "$bin/gsc" \
    "${api_args[@]}" \
    -e '(load (getenv "GENERATION_CONTRACT"))' \
    -e "(run-member-benchmark! \"$phase\")" > "$phase.log" 2>&1
  rg "^MEMBER-PROOF-BENCH $phase " "$phase.log"
  if test "$phase" = group-populate; then
    for name in "${cs[@]}"; do cp "published/$name" "baseline/$name"; done
  elif test "$phase" = group-change; then
    for name in "${cs[@]}"; do cp "published/$name" "baseline/changed-$name"; done
  elif test "$phase" = member-change; then
    for name in "${cs[@]}"; do cmp "baseline/changed-$name" "published/$name"; done
  else
    for name in "${cs[@]}"; do cmp "baseline/$name" "published/$name"; done
  fi
done
test "$(rg -c '^GAMBIT-GENERATED-C-HIT$' member-hit.log)" = "${#inputs[@]}"
test "$(rg -c '^GAMBIT-GENERATED-C-MISS$' member-change.log)" = 1
test "$(rg -c '^GAMBIT-GENERATED-C-HIT$' member-change.log)" = "$((${#inputs[@]}-1))"
"$bin/gsc" -link -flat -o closure.c "${inputs[@]}" > ordinary.log 2>&1
for name in "${cs[@]}"; do cmp "$name" "published/$name"; done
cp closure.c ordinary-link.c
published=()
for name in "${cs[@]}"; do published+=("published/$name"); done
"$bin/gsc" -link -flat -o closure.c "${published[@]}" > member-link.log 2>&1
cmp ordinary-link.c closure.c
for name in "${inputs[@]}"; do cmp "$source/$name" "baseline/$name"; done
for ((index=1; index<${#cs[@]}; index++)); do cmp "baseline/${cs[index]}" "published/${cs[index]}"; done
shasum -a 256 "${published[@]}" ordinary-link.c closure.c > identity.log
printf 'REAL-MEMBER-PROOF-OK modules=%s one-MISS=%s stable-HIT=%s full-C-and-link-parity\n' \
  "${#inputs[@]}" 1 "$((${#inputs[@]}-1))"
