#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../../.." && pwd)
bin=${1:?owned native compiler bin required}
output=${2:?fresh receipt directory required}
home=${3:?owned matching runtime home required}
tools_mode=${4:-per-member}
api_mode=${5:-interpreted}
case "$tools_mode" in per-member|batch) ;; *) exit 2 ;; esac
case "$api_mode" in interpreted|compiled) ;; *) exit 2 ;; esac
case "$bin:$output:$home" in "$root"/.data/*:"$root"/.data/*:"$root"/.data/*) ;; *) exit 2 ;; esac
test ! -e "$output"
cmp "$bin/../include/gambit.h" "$home/include/gambit.h"
mkdir "$output"
trap 'status=$?; printf "%s\n" "$status" > "$output/exit-status.txt"' EXIT
export GERBIL_HOME="$home" PATH="/opt/homebrew/bin:/usr/bin:/bin:$PATH"
export GAMBOPT="~~bin=$bin,~~lib=$home/lib,~~include=$home/include"
export GENERATION_FIXTURE="$output" GENERATION_BIN="$bin"
export GENERATION_IMPLEMENTATION="$root/patches/gerbil-v19-darwin/tests/gambit-generated-c-members.scm"
export GENERATION_CONTRACT="$root/patches/gerbil-v19-darwin/tests/generated_c_member_contract.scm"
export GAMBIT_DARWIN_CLOSED_LINK_MEMBER_PROOF=1 GAMBIT_GENERATED_C_IN_PROCESS_DIGESTS=1
unset GAMBIT_DARWIN_CLOSED_LINK_MEMBER_TOOLS_BATCH
if test "$tools_mode" = batch; then export GAMBIT_DARWIN_CLOSED_LINK_MEMBER_TOOLS_BATCH=1; fi
unset GAMBIT_DARWIN_CLOSED_LINK_REUSE GAMBIT_DARWIN_NATIVE_GENERATED_C
unset GAMBIT_GENERATED_C_PRODUCER_INDEX
api_args=(-e '(load (getenv "GENERATION_IMPLEMENTATION"))')
contract_args=(-e '(run-member-contract!)')
checks=13
if test "$api_mode" = compiled; then
  cmp "$bin/../gsc/gambit-generated-c-members.scm" "$GENERATION_IMPLEMENTATION"
  api_args=(-e '(define reuse-generated-c-members! c#reuse-generated-c-members!)')
  contract_args=(-e '(run-member-contract! #f)')
  checks=11
fi
printf 'tools=%s api=%s\n' "$tools_mode" "$api_mode" > "$output/mode.txt"
/usr/bin/time -p -o "$output/time.txt" gtimeout --signal=TERM --kill-after=1 60s "$bin/gsc" \
  "${api_args[@]}" \
  -e '(load (getenv "GENERATION_CONTRACT"))' \
  "${contract_args[@]}" > "$output/output.log" 2>&1
cat "$output/output.log"
rg -q "^MEMBER-PROOF-CONTRACT-OK $checks$" "$output/output.log"
mkdir "$output/concurrent-a" "$output/concurrent-b"
gtimeout --signal=TERM --kill-after=1 60s "$bin/gsc" \
  "${api_args[@]}" \
  -e '(load (getenv "GENERATION_CONTRACT"))' \
  -e '(run-member-concurrent! "a")' > "$output/concurrent-a.log" 2>&1 &
first=$!
gtimeout --signal=TERM --kill-after=1 60s "$bin/gsc" \
  "${api_args[@]}" \
  -e '(load (getenv "GENERATION_CONTRACT"))' \
  -e '(run-member-concurrent! "b")' > "$output/concurrent-b.log" 2>&1 &
second=$!
first_status=0
second_status=0
wait "$first" || first_status=$?
wait "$second" || second_status=$?
printf '%s\n' "$first_status" > "$output/concurrent-a.exit-status.txt"
printf '%s\n' "$second_status" > "$output/concurrent-b.exit-status.txt"
test "$first_status" = 0 && test "$second_status" = 0
for role in a b; do rg -q "^MEMBER-PROOF-CONCURRENT-OK $role$" "$output/concurrent-$role.log"; done
rg -q '^GAMBIT-GENERATED-C-HIT$' "$output/concurrent-a.log" "$output/concurrent-b.log"
for member in left right; do
  proof="$output/published/$member.c.gambit-member-proof"
  test ! -e "$proof.lock"
  test "$(/usr/bin/stat -f '%Lp' "$proof")" = 600
done
if rg -q 'private-value|MEMBER_PROOF_PRIVATE_CONTEXT' "$output/published"/*.gambit-member-proof; then exit 42; fi
(
  cd "$root"
  shasum -a 256 "${bin#"$root/"}/gsc" \
    patches/gerbil-v19-darwin/tests/gambit-generated-c-members.scm \
    patches/gerbil-v19-darwin/tests/generated_c_member_contract.scm
) > "$output/identity.log"
printf 'MEMBER-PROOF-NATIVE-CONTROLS-OK %s api=%s no-release-admission\n' "$checks" "$api_mode"
printf 'MEMBER-PROOF-NATIVE-CONCURRENCY-OK two-processes reverse-order exact-C-parity\n'
