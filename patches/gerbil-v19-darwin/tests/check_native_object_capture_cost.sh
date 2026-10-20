#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../../.." && pwd)
bin=${1:?owned native-capture candidate bin required}
output=${2:?fresh owned receipt required}
home=${3:?matching runtime home required}
source=${4:?real generated C sample required}
control=${5:-backend}
case "$control" in backend|transport) ;; *) exit 2 ;; esac
case "$bin:$output:$home:$source" in "$root"/.data/*:"$root"/.data/*:"$root"/.data/*:"$root"/.data/*) ;; *) exit 2 ;; esac
test ! -e "$output"
mkdir -p "$output"
trap 'status=$?; printf "%s\n" "$status" > "$output/exit-status.txt"' EXIT
cp "$source" "$output/probe.c"
export GERBIL_HOME="$home" GAMBOPT="~~bin=$bin,~~lib=$home/lib,~~include=$home/include"
export PATH="$bin:/opt/homebrew/bin:/usr/bin:/bin:$PATH"
unset GAMBIT_DARWIN_STATIC_OBJECT_REUSE GAMBIT_DARWIN_STATIC_EXPECTED_SOURCE_SHA
unset GAMBIT_DARWIN_NATIVE_OBJECT_CAPTURE GAMBIT_DARWIN_BOUND_COLD_CAPTURE
unset GAMBIT_DARWIN_NATIVE_OBJECT_CHECK GAMBIT_DARWIN_BOUND_SINGLE_PASS
cd "$output"
"$bin/gsc" -obj -cc-options '-D___DYNAMIC -fPIC' probe.c > ordinary.log 2>&1
cp probe.o ordinary.o
if test "$control" = transport; then
  jobs=$(sysctl -n hw.physicalcpu)
  test "$jobs" -gt 0
  printf 'workers=%s\n' "$jobs" > workers.txt
  shasum -a 256 probe.c ordinary.o "$bin/gsc" "$bin/gambuild-C" \
    "$bin/gambit-static-object-reuse" "$bin/gambit-file-sha256" > identity.log
  export CAPTURE_BIN="$bin" CAPTURE_JOBS="$jobs"
  export CAPTURE_SOURCE_SHA=$("$bin/gambit-file-sha256" --raw probe.c)
  for phase in ordinary-a saved-a native-a native-b saved-b ordinary-b; do
    mkdir "$phase"
    export CAPTURE_PHASE="$phase"
    /usr/bin/time -p -o "$phase.time" bash -c '
      set -euo pipefail
      pids=()
      for ((sample=1; sample<=CAPTURE_JOBS; sample++)); do
        (
          options="-D___DYNAMIC -fPIC"
          case "$CAPTURE_PHASE" in
            saved-*)
              export CORCXXFLAGS_GAMBUILD="-foptimize-sibling-calls"
              options="$options -save-temps=obj" ;;
            native-*)
              export GAMBIT_DARWIN_BOUND_SINGLE_PASS=1 GAMBIT_DARWIN_NATIVE_OBJECT_CAPTURE=1
              export GAMBIT_DARWIN_STATIC_EXPECTED_SOURCE_SHA="$CAPTURE_SOURCE_SHA" ;;
          esac
          "$CAPTURE_BIN/gsc" -obj -o "$CAPTURE_PHASE/$sample.o" -cc-options "$options" probe.c \
            > "$CAPTURE_PHASE/$sample.log" 2>&1
          cmp ordinary.o "$CAPTURE_PHASE/$sample.o"
          case "$CAPTURE_PHASE" in
            native-*)
              rg -q "^GAMBIT-STATIC-BOUND-NATIVE-CAPTURE$" "$CAPTURE_PHASE/$sample.log"
              rg -q "^GAMBIT-STATIC-OBJECT-MISS$" "$CAPTURE_PHASE/$sample.log" ;;
            saved-*) test -s "$CAPTURE_PHASE/$sample.i" && test -s "$CAPTURE_PHASE/$sample.s" ;;
          esac
        ) &
        pids+=("$!")
      done
      status=0
      for pid in "${pids[@]}"; do wait "$pid" || status=1; done
      exit "$status"
    ' > "$phase.log" 2>&1
    printf 'CAPTURE-COST phase=%s workers=%s ' "$phase" "$jobs"
    awk '$1 == "real" {printf "wall=%ss\n", $2}' "$phase.time"
  done
  printf 'NATIVE-CAPTURE-TRANSPORT-COST-OK ordinary/saved/native/native/saved/ordinary exact-object-parity not-package-admission\n'
  exit 0
fi
export GAMBIT_DARWIN_BOUND_SINGLE_PASS=1
export GAMBIT_DARWIN_STATIC_EXPECTED_SOURCE_SHA=$("$bin/gambit-file-sha256" --raw probe.c)
export CAPTURE_BIN="$bin"
for phase in shell-a native-a native-b shell-b; do
  if [[ "$phase" = native-* ]]; then export GAMBIT_DARWIN_NATIVE_OBJECT_CAPTURE=1
  else unset GAMBIT_DARWIN_NATIVE_OBJECT_CAPTURE; fi
  /usr/bin/time -p -o "$phase.time" bash -c '
    set -euo pipefail
    for sample in 1 2 3; do
      rm -f probe.o probe.o.gambit-static-proof
      "$CAPTURE_BIN/gsc" -obj -cc-options "-D___DYNAMIC -fPIC" probe.c
      cmp ordinary.o probe.o
    done
  ' > "$phase.log" 2>&1
  test "$(rg -c '^GAMBIT-STATIC-BOUND-SINGLE-PASS$' "$phase.log")" = 3
  if rg -q 'GAMBIT-STATIC-OBJECT-HIT' "$phase.log"; then exit 1; fi
  if [[ "$phase" = native-* ]]; then
    test "$(rg -c '^GAMBIT-STATIC-BOUND-NATIVE-CAPTURE$' "$phase.log")" = 3
  elif rg -q 'GAMBIT-STATIC-BOUND-NATIVE-CAPTURE' "$phase.log"; then exit 1; fi
done
printf 'NATIVE-CAPTURE-COST-OK matched-generated-C shell/native/native/shell three-fresh-captures-each exact-object-parity\n'
