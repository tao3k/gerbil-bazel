#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../../.." && pwd)
bin=${1:?owned native compiler bin required}
output=${2:?fresh receipt directory required}
home=${3:?owned matching runtime home required}
case "$bin:$output:$home" in "$root"/.data/*:"$root"/.data/*:"$root"/.data/*) ;; *) exit 2 ;; esac
test ! -e "$output"
cmp "$bin/../include/gambit.h" "$home/include/gambit.h"
cmp "$bin/../gsc/gambit-generated-c-members.scm" "$root/patches/gerbil-v19-darwin/tests/gambit-generated-c-members.scm"
mkdir "$output"
trap 'status=$?; printf "%s\n" "$status" > "$output/exit-status.txt"' EXIT
export GERBIL_HOME="$home" PATH="/opt/homebrew/bin:/usr/bin:/bin:$PATH"
export GAMBOPT="~~bin=$bin,~~lib=$home/lib,~~include=$home/include"
export GENERATION_BIN="$bin"
export GENERATION_CONTRACT="$root/patches/gerbil-v19-darwin/tests/generated_c_member_external_mutation.scm"
export GAMBIT_DARWIN_CLOSED_LINK_MEMBER_PROOF=1 GAMBIT_GENERATED_C_IN_PROCESS_DIGESTS=1
export GAMBIT_DARWIN_CLOSED_LINK_MEMBER_TOOLS_BATCH=1
unset GAMBIT_DARWIN_CLOSED_LINK_REUSE GAMBIT_DARWIN_NATIVE_GENERATED_C GAMBIT_GENERATED_C_PRODUCER_INDEX
for mode in include tool; do
  export GENERATION_FIXTURE="$output/$mode"
  mkdir "$GENERATION_FIXTURE"
  "$bin/gsc" -e '(load (getenv "GENERATION_CONTRACT"))' -e '(member-external-setup!)' > "$GENERATION_FIXTURE/setup.log" 2>&1
  env SHLVL=1 _=member-external-control gtimeout --signal=TERM --kill-after=1 30s "$bin/gsc" \
    -e '(load (getenv "GENERATION_CONTRACT"))' -e '(member-external-run! "mutate")' \
    > "$GENERATION_FIXTURE/mutate.log" 2>&1 &
  compiler=$!
  injected=false
  for ((attempt=0; attempt<1000; attempt++)); do
    if test -f "$GENERATION_FIXTURE/published/left.c.gambit-member-proof" && \
       test -d "$GENERATION_FIXTURE/mutate/member-1/right.snapshots"; then
      if test "$mode" = include; then
        printf '(define included-value 29)\n' > "$GENERATION_FIXTURE/value.pending"
        mv "$GENERATION_FIXTURE/value.pending" "$GENERATION_FIXTURE/value.scm"
      else
        printf 'tool-v2\n' > "$GENERATION_FIXTURE/tool.pending"
        mv "$GENERATION_FIXTURE/tool.pending" "$GENERATION_FIXTURE/tool.identity"
      fi
      injected=true
      printf 'MEMBER-EXTERNAL-INJECTED %s\n' "$mode" > "$GENERATION_FIXTURE/injection.log"
      break
    fi
    sleep .01
  done
  status=0
  wait "$compiler" || status=$?
  printf '%s\n' "$status" > "$GENERATION_FIXTURE/mutate.exit-status.txt"
  test "$injected" = true
  test "$status" = 70
  rg -q 'member batch context changed' "$GENERATION_FIXTURE/mutate.log"
  if rg -q '^MEMBER-EXTERNAL-RUN-OK' "$GENERATION_FIXTURE/mutate.log"; then exit 42; fi
  env SHLVL=1 _=member-external-control gtimeout --signal=TERM --kill-after=1 30s "$bin/gsc" \
    -e '(load (getenv "GENERATION_CONTRACT"))' -e '(member-external-run! "retry")' \
    > "$GENERATION_FIXTURE/retry.log" 2>&1
  rg -q '^MEMBER-EXTERNAL-RUN-OK retry$' "$GENERATION_FIXTURE/retry.log"
  for member in left right; do
    test ! -e "$GENERATION_FIXTURE/published/$member.c.gambit-member-proof.lock"
  done
  if test "$mode" = include; then
    test "$(rg -c '^GAMBIT-GENERATED-C-MISS$' "$GENERATION_FIXTURE/retry.log")" = 1
    test "$(rg -c '^GAMBIT-GENERATED-C-HIT$' "$GENERATION_FIXTURE/retry.log")" = 1
  else
    test "$(rg -c '^GAMBIT-GENERATED-C-MISS$' "$GENERATION_FIXTURE/retry.log")" = 2
  fi
  printf 'MEMBER-EXTERNAL-OK %s compiled-coordinator rejected retry-C-parity\n' "$mode"
done
(
  cd "$root"
  shasum -a 256 "${bin#"$root/"}/gsc" \
    patches/gerbil-v19-darwin/tests/gambit-generated-c-members.scm \
    patches/gerbil-v19-darwin/tests/generated_c_member_external_mutation.scm \
    patches/gerbil-v19-darwin/tests/check_generated_c_member_external_mutation.sh
) > "$output/identity.log"
printf 'MEMBER-EXTERNAL-COMPILED-CONTROLS-OK 2 no-release-admission\n'
