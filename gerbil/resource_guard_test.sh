#!/usr/bin/env bash
set -euo pipefail

resolve_runfile() {
  local path=$1
  if [[ "$path" = /* ]]; then
    printf '%s\n' "$path"
  else
    printf '%s/%s\n' "${TEST_SRCDIR:?TEST_SRCDIR is required}" "$path"
  fi
}

gxi=$(resolve_runfile "${1:?gxi path is required}")
guard=$(resolve_runfile "${2:?resource guard path is required}")
root=${TEST_TMPDIR:?TEST_TMPDIR is required}/resource-guard
mkdir -p "$root"

minimum() {
  local minimum_value=$1
  shift
  local value
  for value in "$@"; do
    if (( value < minimum_value )); then
      minimum_value=$value
    fi
  done
  printf '%s\n' "$minimum_value"
}

available_core_count=$(
  "$gxi" \
    -e '(import (only-in :gerbil/compiler/base __available-cores))' \
    -e '(display (max 1 __available-cores))'
)
kibibyte=1024
mebibyte=$((kibibyte * kibibyte))
gibibyte=$((kibibyte * mebibyte))
minimum_memory_per_core_bytes=$((768 * mebibyte))
fixture_system_memory_bytes=$((6 * gibibyte))
fixture_available_memory_bytes=$((4 * gibibyte))
fixture_headroom_bytes=$((768 * mebibyte))
fixture_max_rss_bytes=$((3 * gibibyte))
fixture_available_max_rss_bytes=$((fixture_available_memory_bytes - fixture_headroom_bytes))
normalized_system_memory_bytes=$((32 * gibibyte))
normalized_available_memory_percent=59
normalized_available_memory_bytes=$((normalized_system_memory_bytes * normalized_available_memory_percent / 100))
normalized_headroom_bytes=$((2 * gibibyte))
normalized_max_rss_bytes=$((normalized_available_memory_bytes - normalized_headroom_bytes))
blocked_system_memory_bytes=$((2 * gibibyte))
blocked_available_memory_bytes=$gibibyte
blocked_headroom_bytes=$((512 * mebibyte))
blocked_max_rss_bytes=$gibibyte
explicit_memory_per_core_bytes=$gibibyte
runnable_fixture_memory_per_core_bytes=$((512 * mebibyte))
default_memory_core_limit=$((fixture_max_rss_bytes / minimum_memory_per_core_bytes))
explicit_memory_core_limit=$((fixture_max_rss_bytes / explicit_memory_per_core_bytes))
runnable_fixture_memory_core_limit=$((fixture_max_rss_bytes / runnable_fixture_memory_per_core_bytes))
adaptive_expected=$(minimum "$available_core_count" "$default_memory_core_limit")
explicit_memory_expected=$(minimum "$available_core_count" "$explicit_memory_core_limit")
runnable_pressure_expected=$(minimum \
  "$available_core_count" \
  "$runnable_fixture_memory_core_limit")
runnable_overload_multiplier=4
runnable_saturation_multiplier=12
runnable_overload_processes=$((available_core_count * runnable_overload_multiplier))
runnable_saturation_processes=$((available_core_count * runnable_saturation_multiplier))
short_guard_timeout_seconds=5
timeout_guard_seconds=1
timeout_child_seconds=$((timeout_guard_seconds * 2))
long_running_child_seconds=30
default_sample_seconds=0.05
fast_sample_seconds=0.01
descendant_poll_seconds=0.1
spawner_spawn_interval_seconds=0.02
spawner_poll_seconds=0.05
descendant_poll_attempts=20
spawner_deadline_seconds=3
process_table_snapshot="1 0 0"
runnable_state_snapshot=$'R\nR+\nS\nI'
runnable_state_snapshot_count=2
forced_child_failure_exit_code=99
invalid_max_rss_bytes=1
completed_exit_code=0
rss_limit_exit_code=70
timeout_exit_code=71
admission_blocked_exit_code=72

runnable_core_limit() {
  local runnable_processes=$1
  local other_runnable=$((runnable_processes - 1))
  if (( other_runnable < available_core_count )); then
    printf '%s\n' "$((available_core_count - other_runnable))"
  else
    local proportional_numerator=$((available_core_count * available_core_count))
    local proportional_limit=$((proportional_numerator / other_runnable))
    if (( proportional_limit < 1 )); then
      proportional_limit=1
    fi
    printf '%s\n' "$proportional_limit"
  fi
}

runnable_overload_limit=$(runnable_core_limit "$runnable_overload_processes")
runnable_saturation_limit=$(runnable_core_limit "$runnable_saturation_processes")
runnable_state_snapshot_limit=$(runnable_core_limit "$runnable_state_snapshot_count")

base_host_environment=(
  "GERBIL_BAZEL_GUARD_SYSTEM_MEMORY_BYTES=$fixture_system_memory_bytes"
  "GERBIL_BAZEL_GUARD_AVAILABLE_MEMORY_BYTES=$fixture_available_memory_bytes"
  "GERBIL_BAZEL_GUARD_RSS_HEADROOM_BYTES=$fixture_headroom_bytes"
  "GERBIL_BAZEL_GUARD_SAMPLE_SECONDS=$default_sample_seconds"
  "GERBIL_BAZEL_GUARD_PROCESS_TABLE_SNAPSHOT=$process_table_snapshot"
)
host_environment=(
  "${base_host_environment[@]}"
  "GERBIL_BAZEL_GUARD_RUNNABLE_STATE_SNAPSHOT=$runnable_state_snapshot"
)
common_environment=(
  "${host_environment[@]}"
  "GERBIL_BAZEL_GUARD_MAX_RSS_BYTES=$fixture_max_rss_bytes"
)

assert_build_cores() {
  local name=$1
  local expected=$2
  shift 2
  env "${host_environment[@]}" "$@" \
    /bin/sh -c 'printf "%s\n" "${GERBIL_BUILD_CORES:-unset}"' \
    >"$root/$name.requested-cores"
  env "${host_environment[@]}" "$@" \
    "$gxi" "$guard" "$root/$name.json" "$name" \
    "$short_guard_timeout_seconds" \
    /bin/sh -c 'printf "%s\n" "$GERBIL_BUILD_CORES" >"$1"' guard-child \
    "$root/$name.cores"
  actual=$(cat "$root/$name.cores")
  if [[ "$actual" != "$expected" ]]; then
    requested=$(cat "$root/$name.requested-cores")
    printf '%s: requested GERBIL_BUILD_CORES=%s, expected %s, got %s\n' \
      "$name" "$requested" "$expected" "$actual" >&2
    exit 1
  fi
}

assert_build_cores adaptive-build-cores "$adaptive_expected"
grep -F '"runnableProcessCountAvailable":true' \
  "$root/adaptive-build-cores.json" >/dev/null
grep -F "\"runnableProcessCount\":$runnable_state_snapshot_count" \
  "$root/adaptive-build-cores.json" >/dev/null
assert_build_cores runnable-observation-unavailable "$adaptive_expected" \
  "GERBIL_BAZEL_GUARD_FORCE_RUNNABLE_UNAVAILABLE=1" \
  "GERBIL_BAZEL_GUARD_RUNNABLE_PROCESSES=1"
grep -F '"runnableProcessCountAvailable":false' \
  "$root/runnable-observation-unavailable.json" >/dev/null
grep -F '"runnableProcessCount":0' \
  "$root/runnable-observation-unavailable.json" >/dev/null
assert_build_cores runnable-observation-zero "$adaptive_expected" \
  "GERBIL_BAZEL_GUARD_RUNNABLE_STATE_SNAPSHOT=S"
grep -F '"runnableProcessCountAvailable":true' \
  "$root/runnable-observation-zero.json" >/dev/null
grep -F '"runnableProcessCount":0' \
  "$root/runnable-observation-zero.json" >/dev/null

env "${base_host_environment[@]}" \
  "GERBIL_BAZEL_GUARD_MAX_RSS_BYTES=$fixture_max_rss_bytes" \
  "$gxi" "$guard" "$root/live-runnable-observation.json" \
  live-runnable-observation "$short_guard_timeout_seconds" \
  /bin/sh -c 'exit 0'
grep -F '"runnableProcessCountAvailable":true' \
  "$root/live-runnable-observation.json" >/dev/null

assert_build_cores explicit-memory-per-core "$explicit_memory_expected" \
  "GERBIL_BAZEL_MEMORY_PER_CORE_BYTES=$explicit_memory_per_core_bytes"
assert_build_cores runnable-pressure-does-not-reduce-capacity \
  "$runnable_pressure_expected" \
  "GERBIL_BAZEL_MEMORY_PER_CORE_BYTES=$runnable_fixture_memory_per_core_bytes" \
  "GERBIL_BAZEL_GUARD_RUNNABLE_PROCESSES=$available_core_count"
assert_build_cores runnable-overload-is-advisory "$adaptive_expected" \
  "GERBIL_BAZEL_GUARD_RUNNABLE_PROCESSES=$runnable_overload_processes"
grep -F "\"runnableCoreLimit\":$runnable_overload_limit" \
  "$root/runnable-overload-is-advisory.json" >/dev/null
grep -F '"runnableCoreLimitApplied":false' \
  "$root/runnable-overload-is-advisory.json" >/dev/null
grep -F '"runnableProcessCountAvailable":true' \
  "$root/runnable-overload-is-advisory.json" >/dev/null
grep -F '"admissionAdvisories":["runnable-saturation"]' \
  "$root/runnable-overload-is-advisory.json" >/dev/null
assert_build_cores runnable-saturation-is-advisory "$adaptive_expected" \
  "GERBIL_BAZEL_GUARD_RUNNABLE_PROCESSES=$runnable_saturation_processes"
grep -F "\"requestedBuildCoreCount\":$available_core_count" \
  "$root/runnable-saturation-is-advisory.json" >/dev/null
grep -F "\"effectiveBuildCoreCount\":$adaptive_expected" \
  "$root/runnable-saturation-is-advisory.json" >/dev/null
grep -F "\"runnableCoreLimit\":$runnable_saturation_limit" \
  "$root/runnable-saturation-is-advisory.json" >/dev/null
grep -F '"runnableCoreLimitApplied":false' \
  "$root/runnable-saturation-is-advisory.json" >/dev/null
grep -F '"admissionAdvisories":["runnable-saturation"]' \
  "$root/runnable-saturation-is-advisory.json" >/dev/null

env \
  -u GERBIL_BAZEL_GUARD_SYSTEM_MEMORY_BYTES \
  -u GERBIL_BAZEL_GUARD_MAX_RSS_BYTES \
  PATH=/bin \
  "GERBIL_BAZEL_MEMORY_BYTES=$normalized_system_memory_bytes" \
  "GERBIL_BAZEL_GUARD_AVAILABLE_MEMORY_BYTES=$normalized_available_memory_bytes" \
  "GERBIL_BAZEL_GUARD_RSS_HEADROOM_BYTES=$normalized_headroom_bytes" \
  "GERBIL_BAZEL_GUARD_PROCESS_TABLE_SNAPSHOT=$process_table_snapshot" \
  "$gxi" "$guard" "$root/normalized-system-memory.json" \
  normalized-system-memory "$short_guard_timeout_seconds" \
  /bin/sh -c 'exit 0'
grep -F "\"systemMemoryBytes\":$normalized_system_memory_bytes" \
  "$root/normalized-system-memory.json" >/dev/null
grep -F "\"maxRssBytes\":$normalized_max_rss_bytes" \
  "$root/normalized-system-memory.json" >/dev/null

env "${host_environment[@]}" \
  "GERBIL_BAZEL_MEMORY_BYTES=$normalized_system_memory_bytes" \
  "$gxi" "$guard" "$root/guard-system-memory-override.json" \
  guard-system-memory-override "$short_guard_timeout_seconds" \
  /bin/sh -c 'exit 0'
grep -F "\"systemMemoryBytes\":$fixture_system_memory_bytes" \
  "$root/guard-system-memory-override.json" >/dev/null

available_unavailable_child_marker="$root/available-memory-child-started"
set +e
env \
  -u GERBIL_BAZEL_GUARD_SYSTEM_MEMORY_BYTES \
  -u GERBIL_BAZEL_GUARD_AVAILABLE_MEMORY_BYTES \
  "GERBIL_BAZEL_MEMORY_BYTES=$normalized_system_memory_bytes" \
  GERBIL_BAZEL_GUARD_FORCE_AVAILABLE_MEMORY_UNAVAILABLE=1 \
  "GERBIL_BAZEL_GUARD_RSS_HEADROOM_BYTES=$normalized_headroom_bytes" \
  "GERBIL_BAZEL_GUARD_PROCESS_TABLE_SNAPSHOT=$process_table_snapshot" \
  "$gxi" "$guard" "$root/available-memory-unavailable.json" \
  available-memory-unavailable "$short_guard_timeout_seconds" \
  /bin/sh -c 'touch "$1"; exit "$2"' guard-child \
  "$available_unavailable_child_marker" "$forced_child_failure_exit_code"
available_memory_unavailable_status=$?
set -e
[[ "$available_memory_unavailable_status" -eq "$admission_blocked_exit_code" ]]
[[ ! -e "$available_unavailable_child_marker" ]]
grep -F "\"systemMemoryBytes\":$normalized_system_memory_bytes" \
  "$root/available-memory-unavailable.json" >/dev/null
grep -F '"availableMemoryBytes":0' \
  "$root/available-memory-unavailable.json" >/dev/null
grep -F '"outcome":"blocked-host-pressure"' \
  "$root/available-memory-unavailable.json" >/dev/null
grep -F "\"exitCode\":$admission_blocked_exit_code" \
  "$root/available-memory-unavailable.json" >/dev/null
grep -F '"admissionReasons":["available-memory-unavailable"]' \
  "$root/available-memory-unavailable.json" >/dev/null

env "${host_environment[@]}" \
  GERBIL_BAZEL_GUARD_FORCE_AVAILABLE_MEMORY_UNAVAILABLE=1 \
  "$gxi" "$guard" "$root/explicit-available-precedence.json" \
  explicit-available-precedence "$short_guard_timeout_seconds" \
  /bin/sh -c 'exit 0'
grep -F "\"availableMemoryBytes\":$fixture_available_memory_bytes" \
  "$root/explicit-available-precedence.json" >/dev/null
grep -F '"admissionOutcome":"ready"' \
  "$root/explicit-available-precedence.json" >/dev/null
grep -F '"outcome":"completed"' \
  "$root/explicit-available-precedence.json" >/dev/null

env -u GERBIL_BAZEL_GUARD_MAX_RSS_BYTES "${host_environment[@]}" \
  "$gxi" "$guard" "$root/adaptive-omitted.json" adaptive-omitted \
  "$short_guard_timeout_seconds" \
  /bin/sh -c 'exit 0'
grep -F "\"maxRssBytes\":$fixture_available_max_rss_bytes" \
  "$root/adaptive-omitted.json" >/dev/null

env "${host_environment[@]}" \
  GERBIL_BAZEL_GUARD_MAX_RSS_BYTES=0 \
  "$gxi" "$guard" "$root/adaptive-zero.json" adaptive-zero \
  "$short_guard_timeout_seconds" \
  /bin/sh -c 'exit 0'
grep -F "\"maxRssBytes\":$fixture_available_max_rss_bytes" \
  "$root/adaptive-zero.json" >/dev/null

env "${common_environment[@]}" \
  "$gxi" "$guard" "$root/explicit-within-budget.json" \
  explicit-within-budget "$short_guard_timeout_seconds" \
  /bin/sh -c 'exit 0'
grep -F "\"maxRssBytes\":$fixture_max_rss_bytes" \
  "$root/explicit-within-budget.json" >/dev/null

env "${host_environment[@]}" \
  "GERBIL_BAZEL_GUARD_MAX_RSS_BYTES=$fixture_available_memory_bytes" \
  "$gxi" "$guard" "$root/explicit-capped.json" explicit-capped \
  "$short_guard_timeout_seconds" \
  /bin/sh -c 'exit 0'
grep -F "\"maxRssBytes\":$fixture_available_max_rss_bytes" \
  "$root/explicit-capped.json" >/dev/null

env "${common_environment[@]}" \
  "$gxi" "$guard" "$root/completed.json" completed \
  "$short_guard_timeout_seconds" \
  /bin/sh -c 'exit 0'
grep -F '"admissionOutcome":"ready"' "$root/completed.json" >/dev/null
grep -F '"outcome":"completed"' "$root/completed.json" >/dev/null
grep -F '"schema":"gerbil-bazel.resource-guard-receipt.v1"' \
  "$root/completed.json" >/dev/null

admission_log="$root/admission-before-child.log"
env "${common_environment[@]}" \
  "$gxi" "$guard" "$root/admission-before-child.json" \
  admission-before-child "$short_guard_timeout_seconds" \
  /bin/echo GERBIL_BAZEL_RESOURCE_GUARD_CHILD \
  >"$admission_log" 2>&1
grep -F '"schema":"gerbil-bazel.resource-guard-admission.v1"' \
  "$admission_log" >/dev/null
grep -F "\"requestedBuildCoreCount\":$available_core_count" \
  "$admission_log" >/dev/null
grep -F "\"effectiveBuildCoreCount\":$adaptive_expected" \
  "$admission_log" >/dev/null
grep -F "\"runnableCoreLimit\":$runnable_state_snapshot_limit" \
  "$admission_log" >/dev/null
admission_line=$(
  grep -n -m 1 -F "GERBIL_BAZEL_RESOURCE_GUARD_ADMISSION " \
    "$admission_log" | cut -d: -f1
)
child_line=$(
  grep -n -m 1 -F "GERBIL_BAZEL_RESOURCE_GUARD_CHILD" \
    "$admission_log" | cut -d: -f1
)
final_line=$(
  grep -n -m 1 -F "GERBIL_BAZEL_RESOURCE_GUARD_RECEIPT " \
    "$admission_log" | cut -d: -f1
)
if ! (( admission_line < child_line && child_line < final_line )); then
  printf 'resource guard event order is not admission -> child -> final\n' >&2
  cat "$admission_log" >&2
  exit 1
fi

set +e
env \
  -u GERBIL_BAZEL_GUARD_PROCESS_TABLE_SNAPSHOT \
  -u GERBIL_BAZEL_GUARD_FORCE_PROCESS_TABLE_UNAVAILABLE \
  "GERBIL_BAZEL_GUARD_SYSTEM_MEMORY_BYTES=$fixture_system_memory_bytes" \
  "GERBIL_BAZEL_GUARD_AVAILABLE_MEMORY_BYTES=$fixture_available_memory_bytes" \
  "GERBIL_BAZEL_GUARD_RSS_HEADROOM_BYTES=$fixture_headroom_bytes" \
  "GERBIL_BAZEL_GUARD_MAX_RSS_BYTES=$invalid_max_rss_bytes" \
  "GERBIL_BAZEL_GUARD_SAMPLE_SECONDS=$fast_sample_seconds" \
  "$gxi" "$guard" "$root/rss-limit.json" rss-limit 0 \
  /bin/sleep "$short_guard_timeout_seconds"
rss_limit_status=$?
set -e
[[ "$rss_limit_status" -eq "$rss_limit_exit_code" ]]
grep -F '"outcome":"rss-limit-exceeded"' "$root/rss-limit.json" >/dev/null
grep -F "\"exitCode\":$rss_limit_exit_code" "$root/rss-limit.json" >/dev/null

set +e
env \
  "GERBIL_BAZEL_GUARD_SYSTEM_MEMORY_BYTES=$blocked_system_memory_bytes" \
  "GERBIL_BAZEL_GUARD_AVAILABLE_MEMORY_BYTES=$blocked_available_memory_bytes" \
  "GERBIL_BAZEL_GUARD_RSS_HEADROOM_BYTES=$blocked_headroom_bytes" \
  "GERBIL_BAZEL_GUARD_MAX_RSS_BYTES=$blocked_max_rss_bytes" \
  "GERBIL_BAZEL_GUARD_PROCESS_TABLE_SNAPSHOT=$process_table_snapshot" \
  "$gxi" "$guard" "$root/blocked.json" blocked 0 \
  /bin/sh -c 'exit "$1"' guard-child "$forced_child_failure_exit_code"
blocked_status=$?
set -e
[[ "$blocked_status" -eq "$admission_blocked_exit_code" ]]
grep -F '"admissionOutcome":"blocked-host-pressure"' \
  "$root/blocked.json" >/dev/null
grep -F '"admissionReasons":["insufficient-memory-headroom"]' \
  "$root/blocked.json" >/dev/null

set +e
env "${common_environment[@]}" \
  GERBIL_BAZEL_GUARD_PROCESS_TABLE_SNAPSHOT= \
  GERBIL_BAZEL_GUARD_FORCE_PROCESS_TABLE_UNAVAILABLE=1 \
  "$gxi" "$guard" "$root/unobservable.json" unobservable 0 \
  /bin/sh -c 'exit "$1"' guard-child "$forced_child_failure_exit_code"
unobservable_status=$?
set -e
[[ "$unobservable_status" -eq "$admission_blocked_exit_code" ]]
grep -F '"processTreeRssAvailable":false' "$root/unobservable.json" >/dev/null
grep -F '"admissionReasons":["process-tree-rss-unavailable"]' \
  "$root/unobservable.json" >/dev/null

set +e
env "${common_environment[@]}" \
  "$gxi" "$guard" "$root/timeout.json" timeout "$timeout_guard_seconds" \
  /bin/sleep "$timeout_child_seconds"
timeout_status=$?
set -e
[[ "$timeout_status" -eq "$timeout_exit_code" ]]
grep -F '"outcome":"timeout"' "$root/timeout.json" >/dev/null
grep -F "\"timeoutMs\":$((timeout_guard_seconds * 1000))" \
  "$root/timeout.json" >/dev/null

child_pid_file="$root/timeout-child.pid"
set +e
env "${common_environment[@]}" \
  "$gxi" "$guard" "$root/process-tree-timeout.json" process-tree-timeout \
  "$timeout_guard_seconds" \
  /bin/sh -c 'sleep "$2" & echo $! >"$1"; wait' guard-child \
  "$child_pid_file" "$long_running_child_seconds"
process_tree_timeout_status=$?
set -e
[[ "$process_tree_timeout_status" -eq "$timeout_exit_code" ]]
child_pid=$(cat "$child_pid_file")
for ((attempt = 0; attempt < descendant_poll_attempts; attempt++)); do
  child_state=$(ps -o state= -p "$child_pid" 2>/dev/null | tr -d '[:space:]' || true)
  if [[ -z "$child_state" || "$child_state" == Z* ]]; then
    break
  fi
  sleep "$descendant_poll_seconds"
done
child_state=$(ps -o state= -p "$child_pid" 2>/dev/null | tr -d '[:space:]' || true)
if [[ -n "$child_state" && "$child_state" != Z* ]]; then
  printf 'resource guard left child process %s running after timeout: state=%s\n' \
    "$child_pid" "$child_state" >&2
  exit 1
fi
grep -F '"outcome":"timeout"' "$root/process-tree-timeout.json" >/dev/null

spawner="$root/process-tree-spawner.sh"
spawned_pid_file="$root/process-tree-spawned.pids"
cat >"$spawner" <<'EOF'
#!/bin/sh
set -eu
pid_file=${1:?pid file is required}
long_running_child_seconds=${2:?long-running child seconds are required}
spawn_interval_seconds=${3:?spawn interval seconds are required}
: >"$pid_file"
while :; do
  sleep "$long_running_child_seconds" &
  printf '%s\n' "$!" >>"$pid_file"
  sleep "$spawn_interval_seconds"
done
EOF
chmod +x "$spawner"

set +e
env "${common_environment[@]}" \
  "$gxi" "$guard" "$root/process-tree-spawner-timeout.json" \
  process-tree-spawner-timeout "$timeout_guard_seconds" \
  "$spawner" "$spawned_pid_file" \
  "$long_running_child_seconds" "$spawner_spawn_interval_seconds"
spawner_timeout_status=$?
set -e
[[ "$spawner_timeout_status" -eq "$timeout_exit_code" ]]
[[ -s "$spawned_pid_file" ]]

deadline=$((SECONDS + spawner_deadline_seconds))
while :; do
  all_gone=true
  while IFS= read -r spawned_pid; do
    [[ -n "$spawned_pid" ]] || continue
    spawned_state=$(ps -o state= -p "$spawned_pid" 2>/dev/null | tr -d '[:space:]' || true)
    if [[ -n "$spawned_state" && "$spawned_state" != Z* ]]; then
      all_gone=false
      break
    fi
  done <"$spawned_pid_file"
  if [[ "$all_gone" == true ]]; then
    break
  fi
  if (( SECONDS >= deadline )); then
    printf 'resource guard left a recorded descendant running\n' >&2
    while IFS= read -r spawned_pid; do
      ps -o pid=,ppid=,state=,command= -p "$spawned_pid" >&2 || true
      kill -KILL "$spawned_pid" 2>/dev/null || true
    done <"$spawned_pid_file"
    exit 1
  fi
  sleep "$spawner_poll_seconds"
done
grep -F '"outcome":"timeout"' \
  "$root/process-tree-spawner-timeout.json" >/dev/null
