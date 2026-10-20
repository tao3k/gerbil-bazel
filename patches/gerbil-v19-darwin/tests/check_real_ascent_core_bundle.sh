#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../../.." && pwd)
runtime=${1:?owned matching runtime required}
library=${2:?owned original library required}
fixture=${3:?prepared owned bundle required}
counter=${4:?matching ABI image counter object required}
case "$runtime:$library:$fixture:$counter" in "$root"/.data/*:"$root"/.data/*:"$root"/.data/*:"$root"/.data/*) ;; *) exit 2 ;; esac
test "$(uname -s)" = Darwin
tests="$root/patches/gerbil-v19-darwin/tests"
test "$(cat "$fixture/prepare-exit-status.txt")" = 0
test ! -e "$fixture/run-exit-status.txt"
trap 'status=$?; printf "%s\n" "$status" > "$fixture/run-exit-status.txt"' EXIT
export GERBIL_HOME="$runtime" GERBIL_GSC="$runtime/bin/gsc"
export GAMBOPT="~~bin=$runtime/bin,~~lib=$runtime/lib,~~include=$runtime/include"
export PATH="$runtime/bin:/opt/homebrew/bin:/usr/bin:/bin:$PATH"
unset GAMBIT_DARWIN_NATIVE_GENERATED_C GAMBIT_DARWIN_STATIC_OBJECT_REUSE GAMBIT_DARWIN_NATIVE_OBJECTS
export BUNDLE_COUNTER="$counter"
index=0
for mode in control grouped grouped control; do
  index=$((index + 1))
  export GERBIL_LOADPATH="$fixture/$mode:$library:$runtime/lib"
  /usr/bin/time -p -o "$fixture/$index-$mode.time" gtimeout --signal=TERM --kill-after=1 42s \
    "$runtime/bin/gxi" \
    -e '(load (getenv "BUNDLE_COUNTER"))' \
    -e "(##eval '(define bundle-image-before (bundle-image-count)))" \
    -e '(import :gerbil-ascent/core/dependency-graph :gerbil-ascent/core/expression-plan)' \
    -e "(include \"$tests/real_bundle_core_contract.ss\")" \
    > "$fixture/$index-$mode.log" 2>&1
  cat "$fixture/$index-$mode.log"
  rg -q '^REAL-BUNDLE-CORE-OK image-delta=[0-9]+$' "$fixture/$index-$mode.log"
done
control=$(awk -F= '/^REAL-BUNDLE-CORE-OK / {print $2}' "$fixture/1-control.log")
grouped=$(awk -F= '/^REAL-BUNDLE-CORE-OK / {print $2}' "$fixture/2-grouped.log")
test "$control" = "$(awk -F= '/^REAL-BUNDLE-CORE-OK / {print $2}' "$fixture/4-control.log")"
test "$grouped" = "$(awk -F= '/^REAL-BUNDLE-CORE-OK / {print $2}' "$fixture/3-grouped.log")"
test "$((control - grouped))" = 1
/usr/bin/shasum -a 256 -c "$fixture/input.sha256" > "$fixture/post-run-input-parity.log"
printf 'REAL-ASCENT-CORE-BUNDLE-OK ABBA functional-parity image-reduction=1 input-parity\n'
