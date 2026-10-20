#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../../.." && pwd)
bin=${1:?owned native compiler bin required}
output=${2:?fresh receipt directory required}
home=${3:?owned matching runtime home required}
mode=${4:-include}
case "$mode" in include|tool) ;; *) exit 2 ;; esac
case "$bin:$output:$home" in "$root"/.data/*:"$root"/.data/*:"$root"/.data/*) ;; *) exit 2 ;; esac
test ! -e "$output"
cmp "$bin/../include/gambit.h" "$home/include/gambit.h"
mkdir "$output"
trap 'status=$?; printf "%s\n" "$status" > "$output/exit-status.txt"' EXIT
export GERBIL_HOME="$home" PATH="/opt/homebrew/bin:/usr/bin:/bin:$PATH"
export GAMBOPT="~~bin=$bin,~~lib=$home/lib,~~include=$home/include"
export GENERATION_FIXTURE="$output" GENERATION_BIN="$bin"
export GENERATION_CONTRACT="$root/patches/gerbil-v19-darwin/tests/generated_c_member_external_mutation.scm"
export GAMBIT_DARWIN_CLOSED_LINK_REUSE=1 GAMBIT_GENERATED_C_IN_PROCESS_DIGESTS=1
export GAMBIT_DARWIN_CLOSED_LINK_MEMBER_PROOF=1 GAMBIT_DARWIN_CLOSED_LINK_MEMBER_TOOLS_BATCH=1
unset GAMBIT_DARWIN_NATIVE_GENERATED_C GAMBIT_GENERATED_C_PRODUCER_INDEX
"$bin/gsc" -e '(load (getenv "GENERATION_CONTRACT"))' -e '(member-external-setup!)' > "$output/setup.log" 2>&1
mkdir "$output/second"
mv "$output/right.scm" "$output/second/right.scm"
inputs=(left.scm second/right.scm)
if test "$mode" = tool; then
  mkdir "$output/native-bin"
  cp -p "$bin/gsc" "$bin/gambit-file-sha256" "$output/native-bin/"
  bin="$output/native-bin"
  export GAMBOPT="~~bin=$bin,~~lib=$home/lib,~~include=$home/include"
  # A valid GNU-built replacement has identical SHA behavior but new tool bytes.
  printf '#include "%s"\n__attribute__((used)) int digest_tool_epoch2(void) {return 2;}\n' \
    "$root/patches/gerbil-v19-darwin/tests/gambit-file-sha256.c" > "$output/tool-v2.c"
  /opt/homebrew/bin/gcc-16 -O2 "$output/tool-v2.c" -o "$output/tool-v2"
  test "$("$output/tool-v2" "$output/value.scm")" = "$("$bin/gambit-file-sha256" "$output/value.scm")"
  if cmp -s "$output/tool-v2" "$bin/gambit-file-sha256"; then exit 42; fi
  "$bin/gsc" -c -o "$output/second/right.c" "$output/second/right.scm" > "$output/prepare-C.log" 2>&1
  "$bin/gsc" -e '(load (getenv "GENERATION_CONTRACT"))' -e '(member-external-pad-c!)'
  inputs=(left.scm second/right.c)
fi
cd "$output"
env SHLVL=1 _=closed-member-control gtimeout --signal=TERM --kill-after=1 30s "$bin/gsc" \
  -link -flat -closed-c-binding mutate.binding -o closure.c "${inputs[@]}" \
  > mutate.log 2>&1 &
compiler=$!
injected=false
for ((attempt=0; attempt<1000; attempt++)); do
  triggers=("$output"/mutate.binding.work-*/group-*/member-0/right.snapshots)
  if test "$mode" = tool; then triggers=("$output"/mutate.binding.work-*/pinned-c); fi
  for scratch in "${triggers[@]}"; do
    if test -f left.c.gambit-member-proof && test -e "$scratch"; then
      if test "$mode" = include; then
        printf '(define included-value 29)\n' > value.pending
        mv value.pending value.scm
      else
        mv tool-v2 "$bin/gambit-file-sha256"
      fi
      printf 'CROSS-GROUP-INJECTED %s after-first-group\n' "$mode" > injection.log
      injected=true
      break 2
    fi
  done
  sleep .01
done
status=0
wait "$compiler" || status=$?
printf '%s\n' "$status" > mutate.exit-status.txt
test "$injected" = true
if test "$status" = 0; then
  printf 'CROSS-GROUP-UNSAFE-ACCEPT binding=%s\n' "$(test -f mutate.binding && printf present || printf absent)" >&2
  exit 42
fi
test "$status" = 70
test ! -e mutate.binding
rg -q 'closed link request context changed' mutate.log
env SHLVL=1 _=closed-member-control gtimeout --signal=TERM --kill-after=1 30s "$bin/gsc" \
  -link -flat -closed-c-binding retry.binding -o closure.c "${inputs[@]}" \
  > retry.log 2>&1
test -f retry.binding
cp closure.c member-link.c
cp left.c member-left.c
cp second/right.c member-right.c
env SHLVL=1 _=closed-member-control gtimeout --signal=TERM --kill-after=1 30s "$bin/gsc" \
  -link -flat -o closure.c "${inputs[@]}" > ordinary.log 2>&1
cmp closure.c member-link.c
cmp left.c member-left.c
cmp second/right.c member-right.c
test "$(rg -c '^GAMBIT-GENERATED-C-MISS$' retry.log)" = 1
if test "$mode" = include; then
  test "$(rg -c '^GAMBIT-GENERATED-C-HIT$' retry.log)" = 1
else
  if rg -q '^GAMBIT-GENERATED-C-HIT$' retry.log; then exit 42; fi
fi
test ! -e left.c.gambit-member-proof.lock
test ! -e second/right.c.gambit-member-proof.lock
(
  cd "$root"
  shasum -a 256 "${bin#"$root/"}/gsc" \
    patches/gerbil-v19-darwin/tests/check_closed_member_cross_group.sh \
    patches/gerbil-v19-darwin/tests/generated_c_member_external_mutation.scm
) > identity.log
printf 'CLOSED-MEMBER-CROSS-GROUP-OK %s-denied retry-full-C-link-parity\n' "$mode"
