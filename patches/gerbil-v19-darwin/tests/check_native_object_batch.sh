#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../../.." && pwd)
binary=${1:?owned batch prototype required}
bin=${2:?matching configured compiler bin required}
home=${3:?matching home required}
source=${4:?real generated C required}
output=${5:?fresh owned receipt required}
control=${6:-controls}
case "$control" in controls|environment-contract) ;; *) exit 2 ;; esac
case "$binary:$bin:$home:$source:$output" in "$root"/.data/*:"$root"/.data/*:"$root"/.data/*:"$root"/.data/*:"$root"/.data/*) ;; *) exit 2 ;; esac
test ! -e "$output"
mkdir "$output"
trap 'status=$?; printf "%s\n" "$status" > "$output/exit-status.txt"' EXIT
export PATH="/opt/homebrew/bin:/usr/bin:/bin:$PATH"
unset GAMBIT_DARWIN_STATIC_OBJECT_REUSE GAMBIT_DARWIN_STATIC_EXPECTED_SOURCE_SHA
unset GAMBIT_DARWIN_NATIVE_OBJECT_CAPTURE GAMBIT_DARWIN_NATIVE_OBJECT_CHECK GAMBIT_DARWIN_BOUND_SINGLE_PASS
unset CPATH C_INCLUDE_PATH CPLUS_INCLUDE_PATH NIX_CFLAGS_COMPILE NIX_LDFLAGS
unset CC CFLAGS CPPFLAGS LDFLAGS SDKROOT DEVELOPER_DIR
export GAMBIT_DARWIN_NATIVE_OBJECT_BATCH=1
jobs=$(sysctl -n hw.physicalcpu)
export GERBIL_HOME="$home" GAMBOPT="~~bin=$bin,~~lib=$home/lib,~~include=$home/include"
cp "$source" "$output/probe.c"
cp "$bin/gambuild-C" "$output/tool-receipt"
cd "$output"
# The selected owned build driver is the configuration authority, not a new recipe.
. "$bin/gambuild-C" "" > /dev/null
compiler=${C_COMPILER%% *}
cc1=$("$compiler" -print-prog-name=cc1)
assembler=$("$compiler" -print-prog-name=as)
case "$assembler" in */*) ;; *) assembler=$(command -v "$assembler") ;; esac
apple_as=$(/usr/bin/xcrun --find as)
expected=$("$binary" --raw probe.c)
"$bin/gsc" -obj -cc-options '-D___DYNAMIC -fPIC' probe.c > ordinary.log 2>&1
cp probe.o ordinary.o
dump_environment() {
  rm -f environment environment.nul
  "$binary" --dump-environment "$output/environment.nul" "$output/environment"
}
dump_environment
write_manifest() {
  local path=$1 reverse=${2:-0} failure=${3:-0} extra=${4:-} mixed=${5:-0} sample index options recipe text_env raw_env
  printf '%s\0' gambit-native-object-batch-v3 > "$path"
  for ((index=1; index<=jobs; index++)); do
    sample=$index
    if test "$reverse" = 1; then sample=$((jobs-index+1)); fi
    options="-D___DYNAMIC -fPIC $extra"
    if test "$failure" = 1 && test "$sample" = "$jobs"; then options="$options -fnot-a-real-gcc-option"; fi
    recipe="$C_COMPILER $FLAGS_OPT $FLAGS_OBJ $DEFS_OBJ -I\"$home/include\" -c -o \"$output/$sample.o\" $options \"$output/probe.c\""
    text_env="$output/environment"
    raw_env="$output/environment.nul"
    if test "$mixed" = 1 && test "$sample" -ne "$jobs"; then
      text_env="$output/normal.environment"
      raw_env="$output/normal.environment.nul"
    fi
    printf '%s\0' "$binary" --capture "$output/probe.c" "$output/$sample.o" unused unused "$expected" \
      "$recipe" "$output" "$text_env" "$compiler" \
      "$FLAGS_OPT" "$FLAGS_OBJ" "$DEFS_OBJ" "$options" "$home/include" \
      "$cc1" "$assembler" "$apple_as" "$output/tool-receipt" "$bin/gsc" \
      "$bin/gambit-static-object-reuse" "$binary" "$BUILD_OBJ" "${C_COMPILER#"$compiler"}" \
      "$raw_env" "$output/probe.c" >> "$path"
  done
}
snapshot() {
  local sample
  for ((sample=1; sample<=jobs; sample++)); do
    "$binary" --raw "$sample.o"
    "$binary" --raw "$sample.o.gambit-static-proof"
  done
}
write_manifest "$output/populate.manifest"
/usr/bin/time -p -o populate.time "$binary" --batch "$output/populate.manifest" "$output/populate" "$jobs" > populate.log 2>&1
for ((sample=1; sample<=jobs; sample++)); do cmp ordinary.o "$sample.o"; done
test "$(rg -c '^GAMBIT-STATIC-OBJECT-MISS$' populate.log)" = "$jobs"
rg -q '^GAMBIT-STATIC-OBJECT-BATCH-COMMIT$' populate.log
rg -q '^GAMBIT-STATIC-OBJECT-BATCH-TOOL-SETS 1$' populate.log
snapshot > before.sha
if test "$control" = environment-contract; then
  cp environment normal.environment
  cp environment.nul normal.environment.nul
  saved_exec_prefix=${GCC_EXEC_PREFIX-}
  saved_exec_prefix_set=${GCC_EXEC_PREFIX+1}
  compiler_target=$("$compiler" -dumpmachine)
  compiler_version=$("$compiler" -dumpversion)
  shadow_cc1="$output/tool-shadow/libexec/gcc/$compiler_target/$compiler_version/cc1"
  mkdir -p "$(dirname "$shadow_cc1")" tool-shadow/lib/gcc/current/gcc
  printf '%s\n' '#!/bin/sh' 'exit 91' > "$shadow_cc1"
  chmod +x "$shadow_cc1"
  export GCC_EXEC_PREFIX="$output/tool-shadow/lib/gcc/current/gcc/"
  resolved_request_cc1=$("$compiler" -print-prog-name=cc1)
  test "$resolved_request_cc1" != "$cc1"
  case "$resolved_request_cc1" in "$output"/tool-shadow/*) ;; *) exit 1 ;; esac
  dump_environment
  status=0
  "$binary" --batch "$output/populate.manifest" "$output/tool-resolution" "$jobs" > tool-resolution.log 2>&1 || status=$?
  test "$status" = 2
  if rg -q '^GAMBIT-STATIC-OBJECT-BATCH-COMMIT$' tool-resolution.log; then exit 1; fi
  snapshot > after-tool-resolution.sha
  cmp before.sha after-tool-resolution.sha
  if test "$saved_exec_prefix_set" = 1; then export GCC_EXEC_PREFIX="$saved_exec_prefix"; else unset GCC_EXEC_PREFIX; fi
  dump_environment
  reference_status=0
  env GCC_COMPARE_DEBUG=-fcompare-debug-not-overridden "$bin/gsc" -obj \
    -cc-options '-D___DYNAMIC -fPIC' probe.c > environment-reference.log 2>&1 || reference_status=$?
  test "$reference_status" -ne 0
  env GCC_COMPARE_DEBUG=-fcompare-debug-not-overridden "$binary" --batch "$output/populate.manifest" \
    "$output/parent-poison" "$jobs" > parent-poison.log 2>&1
  test "$(rg -c '^GAMBIT-STATIC-OBJECT-HIT$' parent-poison.log)" = "$jobs"
  export GCC_COMPARE_DEBUG=-fcompare-debug-not-overridden
  dump_environment
  status=0
  "$binary" --batch "$output/populate.manifest" "$output/environment-contract" "$jobs" \
    > environment-contract.log 2>&1 || status=$?
  printf 'ordinary-compiler=%s batch=%s\n' "$reference_status" "$status" > environment-contract-status.txt
  if test "$status" = 0; then
    printf 'BATCH-ENVIRONMENT-DENY declared-failing-compiler-environment-was-not-executed\n' >&2
    exit 42
  fi
  snapshot > after-environment-contract.sha
  cmp before.sha after-environment-contract.sha
  write_manifest "$output/mixed.manifest" 0 0 -fno-inline 1
  status=0
  "$binary" --batch "$output/mixed.manifest" "$output/mixed" "$jobs" > mixed.log 2>&1 || status=$?
  test "$status" = 2
  test "$(rg -c '^GAMBIT-STATIC-OBJECT-MISS$' mixed.log)" = "$((jobs-1))"
  snapshot > after-mixed.sha
  cmp before.sha after-mixed.sha
  env -u GCC_COMPARE_DEBUG "$bin/gsc" -obj -cc-options '-D___DYNAMIC -fPIC -fno-inline' \
    probe.c > mixed-reference.log 2>&1
  for ((sample=0; sample<jobs-1; sample++)); do cmp probe.o "mixed/job-$sample/selected.o"; done
  printf 'BATCH-ENVIRONMENT-CONTRACT-OK failing-request-environment-rejected parent-isolated mixed-job-environments tool-resolution-DENY no-publication\n'
  exit 0
fi
write_manifest "$output/failure.manifest" 0 1
status=0
"$binary" --batch "$output/failure.manifest" "$output/failure" "$jobs" > failure.log 2>&1 || status=$?
test "$status" = 2
if rg -q '^GAMBIT-STATIC-OBJECT-BATCH-COMMIT$' failure.log; then exit 1; fi
snapshot > after-failure.sha
cmp before.sha after-failure.sha
write_manifest "$output/reverse.manifest" 1
"$binary" --batch "$output/populate.manifest" "$output/concurrent-a" "$jobs" > concurrent-a.log 2>&1 &
a=$!
"$binary" --batch "$output/reverse.manifest" "$output/concurrent-b" "$jobs" > concurrent-b.log 2>&1 &
b=$!
status=0
wait "$a" || status=1
wait "$b" || status=1
test "$status" = 0
for phase in concurrent-a concurrent-b; do
  test "$(rg -c '^GAMBIT-STATIC-OBJECT-HIT$' "$phase.log")" = "$jobs"
  rg -q '^GAMBIT-STATIC-OBJECT-BATCH-COMMIT$' "$phase.log"
done
snapshot > after-concurrent.sha
cmp before.sha after-concurrent.sha
printf '%s\n' 'tool-change' >> tool-receipt
"$binary" --batch "$output/populate.manifest" "$output/tool-change" "$jobs" > tool-change.log 2>&1
test "$(rg -c '^GAMBIT-STATIC-OBJECT-MISS$' tool-change.log)" = "$jobs"
for ((sample=1; sample<=jobs; sample++)); do cmp ordinary.o "$sample.o"; done
snapshot > before-mutation.sha
write_manifest "$output/mutation.manifest" 0 0 -fno-inline
"$binary" --batch "$output/mutation.manifest" "$output/mutation" "$jobs" > mutation.log 2>&1 &
mutation_pid=$!
triggered=0
for ((attempt=0; attempt<1000; attempt++)); do
  if test -f mutation/job-0/tools.before && test "$(wc -l < mutation/job-0/tools.before)" -eq 8; then
    printf '%s\n' 'external-mid-request-change' >> tool-receipt
    printf '%s\n' 'after-complete-before-snapshot' > mutation-trigger.txt
    triggered=1
    break
  fi
  if ! kill -0 "$mutation_pid" 2>/dev/null; then break; fi
  sleep .01
done
status=0
wait "$mutation_pid" || status=$?
test "$triggered" = 1 && test "$status" = 2
if rg -q '^GAMBIT-STATIC-OBJECT-BATCH-COMMIT$' mutation.log; then exit 1; fi
snapshot > after-mutation.sha
cmp before-mutation.sha after-mutation.sha
"$binary" --batch "$output/mutation.manifest" "$output/retry" "$jobs" > retry.log 2>&1
test "$(rg -c '^GAMBIT-STATIC-OBJECT-MISS$' retry.log)" = "$jobs"
"$bin/gsc" -obj -cc-options '-D___DYNAMIC -fPIC -fno-inline' probe.c > changed-reference.log 2>&1
for ((sample=1; sample<=jobs; sample++)); do cmp probe.o "$sample.o"; done
export TEST_NATIVE_BATCH_CONTEXT=changed
dump_environment
"$binary" --batch "$output/mutation.manifest" "$output/environment-change" "$jobs" > environment-change.log 2>&1
test "$(rg -c '^GAMBIT-STATIC-OBJECT-MISS$' environment-change.log)" = "$jobs"
for ((sample=1; sample<=jobs; sample++)); do cmp probe.o "$sample.o"; done
snapshot > before-source-change.sha
cp probe.c saved-source.c
printf '\n%s\n' '/* source changed after source binding */' >> probe.c
status=0
"$binary" --batch "$output/mutation.manifest" "$output/source-change" "$jobs" > source-change.log 2>&1 || status=$?
test "$status" = 2 && test ! -e source-change
mv saved-source.c probe.c
snapshot > after-source-change.sha
cmp before-source-change.sha after-source-change.sha
shasum -a 256 probe.c ordinary.o "$binary" > identity.log
printf 'NATIVE-OBJECT-BATCH-OK workers=%s ordinary-parity failure-no-publication reverse-concurrent-HIT tool-change-MISS external-mutation-DENY option-change-retry-parity environment-MISS source-binding-DENY\n' "$jobs"
