#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../../.." && pwd)
runtime=${1:?owned runtime required}
hashbin=${2:?owned digest helper bin required}
output=${3:?fresh owned fixture required}
policy=${4:-original}
case "$runtime:$hashbin:$output" in "$root"/.data/*:"$root"/.data/*:"$root"/.data/*) ;; *) exit 2 ;; esac
case "$policy" in original|snapshot|patched|native) ;; *) exit 2 ;; esac
test ! -e "$output"
mkdir -p "$output/published" "$output/control" "$output/work" "$output/repeat"
export GENERATION_FIXTURE="$output" GENERATION_HASH_TOOL="$hashbin/gambit-file-sha256"
export GENERATION_JOURNAL="$root/patches/gerbil-v19-darwin/tests/gambit-generated-c-reads.scm"
if test "$policy" = patched; then
  export GENERATION_JOURNAL=${5:?owned patched reader required}
  case "$GENERATION_JOURNAL" in "$root"/.data/*) ;; *) exit 2 ;; esac
  test -f "$GENERATION_JOURNAL" && test ! -L "$GENERATION_JOURNAL"
fi
export GENERATION_IMPLEMENTATION="$root/patches/gerbil-v19-darwin/tests/gambit-generated-c-closure.scm"
export GENERATION_CONTRACT="$root/patches/gerbil-v19-darwin/tests/generated_c_read_race_contract.scm"
home=$runtime
if test "$policy" = native; then
  home=${5:?owned matching native runtime required}
  case "$home" in "$root"/.data/*) ;; *) exit 2 ;; esac
fi
export GAMBOPT="~~bin=$runtime/bin,~~lib=$home/lib,~~include=$home/include"
unset GAMBIT_GENERATED_C_BATCH_DIGESTS GENERATION_EXPECT_SNAPSHOT GENERATION_NATIVE
extra=()
if test "$policy" = patched; then export GENERATION_EXPECT_SNAPSHOT=1; fi
base=(-e '(load (getenv "GENERATION_JOURNAL"))' -e '(load (getenv "GENERATION_IMPLEMENTATION"))')
if test "$policy" = native; then
  export GENERATION_NATIVE=1 GENERATION_EXPECT_SNAPSHOT=1
  base=()
fi
if test "$policy" = snapshot; then
  export GENERATION_EXPECT_SNAPSHOT=1
  export GENERATION_SNAPSHOT_JOURNAL="$root/patches/gerbil-v19-darwin/tests/gambit-generated-c-snapshot-reads.scm"
  extra=(-e '(load (getenv "GENERATION_SNAPSHOT_JOURNAL"))')
fi
set +e
"$runtime/bin/gsc" "${base[@]}" "${extra[@]}" \
  -e '(load (getenv "GENERATION_CONTRACT"))' -e '(run-generated-c-read-race-contract!)' \
  > "$output/output.log" 2>&1
status=$?
set -e
printf '%s\n' "$status" > "$output/exit-status.txt"
cat "$output/output.log"
exit "$status"
