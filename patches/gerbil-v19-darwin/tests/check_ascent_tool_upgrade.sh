#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../../.." && pwd)
workspace=${1:?fresh prepared owned ASCENT workspace required}
receipt=${2:?fresh owned receipt required}
case "$workspace:$receipt" in "$root"/.data/*:"$root"/.data/*) ;; *) exit 2 ;; esac
test ! -e "$receipt"
mkdir "$receipt"
trap 'status=$?; printf "%s\n" "$status" > "$receipt/exit-status.txt"' EXIT
compiler="$workspace/toolchain/bin/compiler"
test -f "$compiler" && test ! -L "$compiler"
unset GCC_EXEC_PREFIX COMPILER_PATH
test -f "$("$compiler" -print-prog-name=cc1)"
test -f "$("$compiler" -print-file-name=libemutls_w.a)"
test "$($compiler -dumpmachine)" = "$(/opt/homebrew/bin/gcc-16 -dumpmachine)"
/usr/bin/shasum -a 256 /opt/homebrew/bin/gcc-16 > "$receipt/installed-compiler-before.sha256"
/usr/bin/shasum -a 256 "$compiler" > "$receipt/private-compiler-before.sha256"
tests="$root/patches/gerbil-v19-darwin/tests"
for phase in establish changed unchanged; do
  if test "$phase" = changed; then
    # Only the private copy is mutated; executed compiler code remains unchanged.
    printf '\nprivate-ascent-tool-content-invalidation\n' >> "$compiler"
    /usr/bin/shasum -a 256 "$compiler" > "$receipt/private-compiler-after.sha256"
    if cmp -s "$receipt/private-compiler-before.sha256" "$receipt/private-compiler-after.sha256"; then exit 2; fi
  fi
  bash "$tests/run_isolated_ascent_static_reuse.sh" "$workspace" "$receipt/$phase" \
    candidate positive-plan external 135 "$compiler" > "$receipt/$phase-launch.log" 2>&1
  log="$receipt/$phase/output.log"
  test "$(rg -c '^CASE ' "$log")" = 30
  rg -q '^OK$' "$log"
  printf 'ASCENT-TOOL-PHASE-OK %s cases=30\n' "$phase"
  if test "$phase" = unchanged; then
    rg -q '^NATIVE-ENTRY-CACHE-HIT$' "$log"
    if rg -q '^NATIVE-ENTRY-CACHE-MISS$|GAMBIT-STATIC-OBJECT-(MISS|HIT)' "$log"; then exit 2; fi
  else
    rg -q '^NATIVE-ENTRY-CACHE-MISS$' "$log"
    rg -q '^GAMBIT-STATIC-OBJECT-MISS$' "$log"
    if test "$phase" = changed && rg -q 'GAMBIT-STATIC-OBJECT-HIT' "$log"; then exit 2; fi
  fi
done
/usr/bin/shasum -a 256 /opt/homebrew/bin/gcc-16 > "$receipt/installed-compiler-after.sha256"
cmp "$receipt/installed-compiler-before.sha256" "$receipt/installed-compiler-after.sha256"
printf 'ASCENT-TOOL-UPGRADE-OK three-native-runs 30-cases-each actual-GNU-content-invalidation installed-compiler-unchanged\n'
