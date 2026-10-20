#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../../.." && pwd)
workspace=${1:?isolated workspace required}
receipt=${2:?fresh receipt directory required}
mode=${3:?control, candidate, native, closed-link, member-link, fresh-produced or recipe-proof required}
scope=${4:-positive-plan}
case "$workspace:$receipt" in "$root"/.data/*:"$root"/.data/*) ;; *) exit 2 ;; esac
case "$mode" in control|candidate|native|closed-link|member-link|fresh-produced|recipe-proof) ;; *) exit 2 ;; esac
case "$scope" in positive-plan|all) ;; *) exit 2 ;; esac
deadline=${6:-0}
command_prefix=()
if test "$deadline" != 0; then
  [[ "$deadline" =~ ^[1-9][0-9]*$ ]] || exit 2
  command -v gtimeout >/dev/null
  command_prefix=(gtimeout --signal=TERM --kill-after=1 "${deadline}s")
fi
test ! -e "$receipt"
mkdir -p "$receipt"
cd "$workspace/project"
test "$(git rev-parse HEAD)" = 21e3638687d42ecfc36acebb28991987435ebc60
expected_source_diff=${8:-}
verify_source_fixture() {
  if test -z "$expected_source_diff"; then
    test -z "$(git status --porcelain --untracked-files=no)"
  else
    [[ "$expected_source_diff" =~ ^[0-9a-f]{64}$ ]] || return 2
    local actual
    actual=$(git diff --binary HEAD | /usr/bin/shasum -a 256)
    test "${actual%% *}" = "$expected_source_diff"
  fi
}
verify_source_fixture
export GERBIL_HOME="$workspace/toolchain"
diagnostic_bin=${9:-}
selected_bin="$GERBIL_HOME/bin"
if test -n "$diagnostic_bin"; then
  case "$diagnostic_bin" in "$root"/.data/*) ;; *) exit 2 ;; esac
  if test ! -d "$diagnostic_bin" || test -L "$diagnostic_bin"; then exit 2; fi
  for tool in gsc compiler gcc gambuild-C gambit-static-object-reuse gambit-file-sha256; do
    if test ! -f "$diagnostic_bin/$tool" || test -L "$diagnostic_bin/$tool"; then exit 2; fi
  done
  test -n "${GAMBIT_NATIVE_PHASE_TRACE-}"
  selected_bin=$diagnostic_bin
fi
export GERBIL_GSC="$selected_bin/gsc"
export GERBIL_GCC=${7:-/opt/homebrew/bin/gcc-16}
if test "$GERBIL_GCC" != /opt/homebrew/bin/gcc-16; then
  test "${GERBIL_GCC%/*}" = "$selected_bin" || exit 2
  test -f "$GERBIL_GCC" && test ! -L "$GERBIL_GCC" && test -x "$GERBIL_GCC"
fi
test ! -L "$GERBIL_HOME/bin"
# The consumer's entry proof resolves gcc through PATH, not GERBIL_GCC.
if test -n "$diagnostic_bin"; then
  test "$GERBIL_GCC" = "$diagnostic_bin/compiler"
elif test -e "$GERBIL_HOME/bin/gcc" || test -L "$GERBIL_HOME/bin/gcc"; then
  test -L "$GERBIL_HOME/bin/gcc"
  test "$(readlink "$GERBIL_HOME/bin/gcc")" = "$GERBIL_GCC"
else
  ln -s "$GERBIL_GCC" "$GERBIL_HOME/bin/gcc"
fi
export GERBIL_PATH="$workspace/dependencies/prefix"
export PATH="$GERBIL_HOME/bin:/opt/homebrew/bin:/usr/bin:/bin:$PATH"
if test -n "$diagnostic_bin"; then export PATH="$diagnostic_bin:$PATH"; fi
runtime_bin=${10:-}
selected_gxi="$GERBIL_HOME/bin/gxi"
if test -n "$runtime_bin"; then
  case "$runtime_bin" in "$root"/.data/*) ;; *) exit 2 ;; esac
  test -d "$runtime_bin" && test ! -L "$runtime_bin"
  test -f "$runtime_bin/gxi" && test ! -L "$runtime_bin/gxi" && test -x "$runtime_bin/gxi"
  test -n "${GAMBIT_DARWIN_DRIVER_OVERLAY-}"
  case "$GAMBIT_DARWIN_DRIVER_OVERLAY" in "$root"/.data/*) ;; *) exit 2 ;; esac
  test -f "$GAMBIT_DARWIN_DRIVER_OVERLAY" && test ! -L "$GAMBIT_DARWIN_DRIVER_OVERLAY"
  export PATH="$runtime_bin:$PATH"
  selected_gxi="$runtime_bin/gxi"
  /usr/bin/shasum -a 256 "$selected_gxi" "$GAMBIT_DARWIN_DRIVER_OVERLAY" > "$receipt/overlay-before.sha256"
fi
test "$(command -v gcc)" = "$selected_bin/gcc"
test -x "$GERBIL_HOME/bin/gxi"
test "$(command -v gxi)" = "$selected_gxi" || {
  printf 'ASCENT-TOOLCHAIN-DENY gxi escaped selected toolchain\n' >&2
  exit 2
}
export GERBIL_BUILD_CORES="$(getconf NPROCESSORS_ONLN)"
export GAMBOPT="~~bin=$selected_bin,~~lib=$GERBIL_HOME/lib,~~include=$GERBIL_HOME/include"
unset GAMBIT_DARWIN_STATIC_OBJECT_REUSE
if test "$mode" != control; then export GAMBIT_DARWIN_STATIC_OBJECT_REUSE=1; fi
unset GAMBIT_DARWIN_NATIVE_GENERATED_C GAMBIT_GENERATED_C_BATCH_DIGESTS GAMBIT_GENERATED_C_PRODUCER_INDEX
unset GAMBIT_GENERATED_C_IN_PROCESS_DIGESTS
unset GAMBIT_DARWIN_CLOSED_LINK_REUSE GAMBIT_DARWIN_STATIC_EXPECTED_SOURCE_SHA
unset GAMBIT_DARWIN_CLOSED_LINK_FRESH_OBJECTS GAMBIT_DARWIN_CLOSED_LINK_PRODUCER_PROOF
unset GAMBIT_DARWIN_CLOSED_LINK_RECIPE_PROOF
unset GAMBIT_DARWIN_CLOSED_LINK_MEMBER_PROOF GAMBIT_DARWIN_CLOSED_LINK_MEMBER_TOOLS_BATCH
unset GAMBIT_DARWIN_BOUND_SINGLE_PASS GAMBIT_DARWIN_BOUND_COLD_CAPTURE
unset GAMBIT_DARWIN_NATIVE_OBJECT_CAPTURE GAMBIT_DARWIN_NATIVE_OBJECT_CHECK
if test "$mode" = native; then
  export GAMBIT_DARWIN_NATIVE_GENERATED_C=1 GAMBIT_GENERATED_C_BATCH_DIGESTS=1
  if test "${5:-external}" = native-digests; then
    export GAMBIT_GENERATED_C_IN_PROCESS_DIGESTS=1
  elif test "${5:-external}" != external; then
    exit 2
  fi
  mkdir -p "$receipt/producer-index"
  export GAMBIT_GENERATED_C_PRODUCER_INDEX="$receipt/producer-index"
fi
if test "$mode" = closed-link || test "$mode" = member-link || test "$mode" = fresh-produced || test "$mode" = recipe-proof; then
  export GAMBIT_DARWIN_CLOSED_LINK_REUSE=1 GAMBIT_GENERATED_C_IN_PROCESS_DIGESTS=1
fi
if test "$mode" = member-link; then
  export GAMBIT_DARWIN_CLOSED_LINK_MEMBER_PROOF=1 GAMBIT_DARWIN_CLOSED_LINK_MEMBER_TOOLS_BATCH=1
fi
if test "$mode" = fresh-produced; then
  export GAMBIT_DARWIN_CLOSED_LINK_FRESH_OBJECTS=1 GAMBIT_DARWIN_BOUND_SINGLE_PASS=1
  export GAMBIT_DARWIN_NATIVE_OBJECT_CAPTURE=1 GAMBIT_DARWIN_NATIVE_OBJECT_CHECK=1
fi
if test "$mode" = recipe-proof; then
  export GAMBIT_DARWIN_CLOSED_LINK_PRODUCER_PROOF=1 GAMBIT_DARWIN_CLOSED_LINK_RECIPE_PROOF=1
  export GAMBIT_DARWIN_BOUND_SINGLE_PASS=1
  export GAMBIT_DARWIN_NATIVE_OBJECT_CAPTURE=1 GAMBIT_DARWIN_NATIVE_OBJECT_CHECK=1
fi
printf 'ASCENT-ISOLATED-MODE %s\n' "$mode"
printf 'ASCENT-ISOLATED-SCOPE %s\n' "$scope"
printf 'ASCENT-WHOLE-TASK-DEADLINE %s\n' "$deadline"
printf 'ENTRY-COMPILER-IDENTITY-ALIGNED\n'
if test -n "$diagnostic_bin" && test -x "$diagnostic_bin/clock"; then
  "$diagnostic_bin/clock" --clock > "$receipt/task-begin.ns"
fi
/usr/bin/shasum -a 256 "$GERBIL_HOME/bin/gerbil" "$GERBIL_GSC" \
  "$selected_bin/gambuild-C" "$selected_bin/gambit-static-object-reuse" > "$receipt/toolchain.sha256"
# The repository's own Scheme qualifier owns compilation, Cases and deadlines.
set +e
if test "$scope" = all; then
  /usr/bin/time -p -o "$receipt/time.txt" ${command_prefix[@]+"${command_prefix[@]}"} just test-native-suite auto 2>&1 | tee "$receipt/output.log"
  status=${PIPESTATUS[0]}
else
  /usr/bin/time -p -o "$receipt/time.txt" ${command_prefix[@]+"${command_prefix[@]}"} just test-native \
    t/qualification/ascent-positive-plan-test.ss 2>&1 | tee "$receipt/output.log"
  status=${PIPESTATUS[0]}
fi
set -e
if test -n "$diagnostic_bin" && test -x "$diagnostic_bin/clock"; then
  "$diagnostic_bin/clock" --clock > "$receipt/task-end.ns"
fi
printf '%s\n' "$status" > "$receipt/exit-status.txt"
if test -n "$runtime_bin"; then
  /usr/bin/shasum -a 256 "$selected_gxi" "$GAMBIT_DARWIN_DRIVER_OVERLAY" > "$receipt/overlay-after.sha256"
  cmp "$receipt/overlay-before.sha256" "$receipt/overlay-after.sha256"
fi
verify_source_fixture
if test "$status" = 0 && test "$scope" = all; then
  export NATIVE_REGISTRY_SOURCE="$workspace/project/.cache/ascent/native-library/test-pool.ss"
  export NATIVE_REGISTRY_INVENTORY="$receipt/modules.txt"
  "$GERBIL_GSC" -e "(load \"$root/patches/gerbil-v19-darwin/tests/export_native_registry_inventory.scm\")" \
    -e '(export-native-registry-inventory! (getenv "NATIVE_REGISTRY_SOURCE") (getenv "NATIVE_REGISTRY_INVENTORY"))'
fi
exit "$status"
