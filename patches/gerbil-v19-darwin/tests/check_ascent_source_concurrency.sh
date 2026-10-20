#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../../.." && pwd)
workspace=${1:?owned prepared ASCENT workspace required}
receipt=${2:?fresh owned receipt required}
expected=${3:?exact tracked source fixture diff SHA256 required}
case "$workspace:$receipt" in "$root"/.data/*:"$root"/.data/*) ;; *) exit 2 ;; esac
test ! -e "$receipt"
mkdir "$receipt"
trap 'status=$?; printf "%s\n" "$status" > "$receipt/exit-status.txt"' EXIT
compiler="$workspace/toolchain/bin/compiler"
tests="$root/patches/gerbil-v19-darwin/tests"
unset GCC_EXEC_PREFIX COMPILER_PATH
git -C "$workspace/project" diff --binary HEAD > "$receipt/source-fixture.diff"
actual=$(/usr/bin/shasum -a 256 "$receipt/source-fixture.diff")
test "${actual%% *}" = "$expected"
for index in 1 2; do
  bash "$tests/run_isolated_ascent_static_reuse.sh" "$workspace" "$receipt/$index" \
    candidate positive-plan external 135 "$compiler" "$expected" > "$receipt/$index-launch.log" 2>&1 &
  if test "$index" = 1; then first=$!; else second=$!; fi
done
set +e
wait "$first"; first_status=$?
wait "$second"; second_status=$?
set -e
printf '%s %s\n' "$first_status" "$second_status" > "$receipt/child-statuses.txt"
test "$first_status" = 0 && test "$second_status" = 0
misses=0 hits=0
for index in 1 2; do
  log="$receipt/$index/output.log"
  test "$(rg -c '^CASE ' "$log")" = 30
  rg -q '^OK$' "$log"
  if rg -q '^NATIVE-ENTRY-CACHE-MISS$' "$log"; then
    misses=$((misses + 1))
  fi
  if rg -q '^NATIVE-ENTRY-CACHE-HIT$' "$log"; then
    hits=$((hits + 1))
    if rg -q 'GAMBIT-STATIC-OBJECT-(MISS|HIT)' "$log"; then exit 2; fi
  fi
done
test "$misses" = 1 && test "$hits" = 1
printf 'ASCENT-SOURCE-CONCURRENCY-OK two-native-runs 30-cases-each one-entry-MISS one-entry-HIT exact-source-diff\n'
