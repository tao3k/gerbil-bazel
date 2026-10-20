#!/usr/bin/env bash
# Matched native request overhead only, not a whole-package benchmark.
set -euo pipefail
root=$(cd "$(dirname "$0")/../../.." && pwd)
bin=${1:?owned configured request driver bin required}
home=${2:?matching toolchain home required}
source=${3:?real generated C required}
output=${4:?fresh owned receipt required}
case "$bin:$home:$source:$output" in "$root"/.data/*:"$root"/.data/*:"$root"/.data/*:"$root"/.data/*) ;; *) exit 2 ;; esac
test ! -e "$output"
mkdir "$output"
trap 'status=$?; printf "%s\n" "$status" > "$output/exit-status.txt"' EXIT
jobs=$(sysctl -n hw.physicalcpu)
printf '%s\n' "$jobs" > "$output/workers.txt"
export PATH="$bin:/opt/homebrew/bin:/usr/bin:/bin:$PATH"
export GERBIL_HOME="$home" GAMBOPT="~~bin=$bin,~~lib=$home/lib,~~include=$home/include"
export GAMBIT_DARWIN_NATIVE_OBJECT_BATCH=1 GAMBIT_DARWIN_NATIVE_OBJECT_CAPTURE=1
export GAMBIT_DARWIN_NATIVE_OBJECT_CHECK=1 GAMBIT_DARWIN_BOUND_SINGLE_PASS=1
unset GAMBIT_DARWIN_OBJECT_PREPARE_DIRECTORY GAMBIT_DARWIN_STATIC_OBJECT_REUSE
unset CPATH C_INCLUDE_PATH CPLUS_INCLUDE_PATH NIX_CFLAGS_COMPILE NIX_LDFLAGS
unset CC CFLAGS CPPFLAGS LDFLAGS SDKROOT DEVELOPER_DIR GCC_COMPARE_DEBUG GCC_EXEC_PREFIX
export GAMBIT_DARWIN_STATIC_EXPECTED_SOURCE_SHA=$("$bin/gambit-file-sha256" --raw "$source")
for ((job=1; job<=jobs; job++)); do
  mkdir "$output/$job"
  cp -p "$source" "$output/$job/probe.c"
done
run_phase() {
  local phase=$1 kind=$2
  /usr/bin/time -p -o "$output/$phase.time" bash -c '
    set -euo pipefail
    phase=$1
    kind=$2
    bin=$3
    output=$4
    jobs=$5
    pids=()
    for ((job=1; job<=jobs; job++)); do
      (
        if test "$kind" = batch; then
          export GAMBIT_DARWIN_OBJECT_PREPARE_DIRECTORY="$output/$job/$phase.prepared"
        fi
        "$bin/gsc" -obj -cc-options "-D___DYNAMIC -fPIC" "$output/$job/probe.c" \
          > "$output/$job/$phase.log" 2>&1
      ) &
      pids+=("$!")
    done
    failed=0
    for pid in "${pids[@]}"; do wait "$pid" || failed=1; done
    test "$failed" = 0
    if test "$kind" = batch; then
      printf "%s\000" gambit-native-object-batch-v3 > "$output/$phase.request"
      for ((job=1; job<=jobs; job++)); do
        cat "$output/$job/$phase.prepared/record" >> "$output/$phase.request"
      done
      "$bin/gambit-file-sha256" --batch "$output/$phase.request" "$output/$phase.stage" "$jobs" \
        > "$output/$phase.batch.log" 2>&1
    fi
  ' object-request-cost "$phase" "$kind" "$bin" "$output" "$jobs"
}
run_phase populate ordinary
for ((job=1; job<=jobs; job++)); do
  cp "$output/$job/probe.o" "$output/$job/reference.o"
  cp "$output/$job/probe.o.gambit-static-proof" "$output/$job/reference.proof"
done
for phase in ordinary-1 batch-1 batch-2 ordinary-2; do
  kind=${phase%-*}
  run_phase "$phase" "$kind"
  for ((job=1; job<=jobs; job++)); do
    cmp "$output/$job/reference.o" "$output/$job/probe.o"
    cmp "$output/$job/reference.proof" "$output/$job/probe.o.gambit-static-proof"
    if test "$kind" = ordinary; then
      rg -q '^GAMBIT-STATIC-OBJECT-HIT$' "$output/$job/$phase.log"
    else
      rg -q '^GAMBIT-STATIC-OBJECT-REQUEST-PREPARED$' "$output/$job/$phase.log"
    fi
  done
  if test "$kind" = batch; then
    test "$(rg -c '^GAMBIT-STATIC-OBJECT-HIT$' "$output/$phase.batch.log")" = "$jobs"
    rg -q '^GAMBIT-STATIC-OBJECT-BATCH-COMMIT$' "$output/$phase.batch.log"
  fi
  printf 'OBJECT-REQUEST-COST phase=%s workers=%s ' "$phase" "$jobs"
  awk '/^real / {print "seconds=" $2}' "$output/$phase.time"
done
shasum -a 256 "$source" "$bin/gsc" "$bin/gambuild-C" \
  "$bin/gambit-object-request-prepare" "$bin/gambit-file-sha256" > "$output/identity.log"
printf 'OBJECT-REQUEST-COST-OK all-HIT exact-object-proof-parity matched-ABBA component-only\n'
