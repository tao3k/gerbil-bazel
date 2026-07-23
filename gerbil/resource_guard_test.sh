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

host_environment=(
  GERBIL_BAZEL_GUARD_SYSTEM_MEMORY_BYTES=6442450944
  GERBIL_BAZEL_GUARD_AVAILABLE_MEMORY_BYTES=4294967296
  GERBIL_BAZEL_GUARD_RSS_HEADROOM_BYTES=805306368
  GERBIL_BAZEL_GUARD_RUNNABLE_PROCESSES=1
  GERBIL_BAZEL_GUARD_SAMPLE_SECONDS=0.05
  "GERBIL_BAZEL_GUARD_PROCESS_TABLE_SNAPSHOT=1 0 0"
)
common_environment=(
  "${host_environment[@]}"
  GERBIL_BAZEL_GUARD_MAX_RSS_BYTES=3221225472
)

env \
  -u GERBIL_BAZEL_GUARD_SYSTEM_MEMORY_BYTES \
  -u GERBIL_BAZEL_GUARD_MAX_RSS_BYTES \
  PATH=/bin \
  GERBIL_BAZEL_MEMORY_BYTES=34359738368 \
  GERBIL_BAZEL_GUARD_AVAILABLE_MEMORY_BYTES=20272245637 \
  GERBIL_BAZEL_GUARD_RSS_HEADROOM_BYTES=2147483648 \
  GERBIL_BAZEL_GUARD_RUNNABLE_PROCESSES=1 \
  "GERBIL_BAZEL_GUARD_PROCESS_TABLE_SNAPSHOT=1 0 0" \
  "$gxi" "$guard" "$root/normalized-system-memory.json" \
  normalized-system-memory 5 \
  /bin/sh -c 'exit 0'
grep -F '"systemMemoryBytes":34359738368' \
  "$root/normalized-system-memory.json" >/dev/null
grep -F '"maxRssBytes":18124761989' \
  "$root/normalized-system-memory.json" >/dev/null

env "${host_environment[@]}" \
  GERBIL_BAZEL_MEMORY_BYTES=34359738368 \
  "$gxi" "$guard" "$root/guard-system-memory-override.json" \
  guard-system-memory-override 5 \
  /bin/sh -c 'exit 0'
grep -F '"systemMemoryBytes":6442450944' \
  "$root/guard-system-memory-override.json" >/dev/null

available_unavailable_child_marker="$root/available-memory-child-started"
set +e
env \
  -u GERBIL_BAZEL_GUARD_SYSTEM_MEMORY_BYTES \
  -u GERBIL_BAZEL_GUARD_AVAILABLE_MEMORY_BYTES \
  GERBIL_BAZEL_MEMORY_BYTES=34359738368 \
  GERBIL_BAZEL_GUARD_FORCE_AVAILABLE_MEMORY_UNAVAILABLE=1 \
  GERBIL_BAZEL_GUARD_RSS_HEADROOM_BYTES=2147483648 \
  GERBIL_BAZEL_GUARD_RUNNABLE_PROCESSES=1 \
  "GERBIL_BAZEL_GUARD_PROCESS_TABLE_SNAPSHOT=1 0 0" \
  "$gxi" "$guard" "$root/available-memory-unavailable.json" \
  available-memory-unavailable 5 \
  /bin/sh -c 'touch "$1"; exit 99' guard-child \
  "$available_unavailable_child_marker"
available_memory_unavailable_status=$?
set -e
[[ "$available_memory_unavailable_status" -eq 72 ]]
[[ ! -e "$available_unavailable_child_marker" ]]
grep -F '"systemMemoryBytes":34359738368' \
  "$root/available-memory-unavailable.json" >/dev/null
grep -F '"availableMemoryBytes":0' \
  "$root/available-memory-unavailable.json" >/dev/null
grep -F '"outcome":"blocked-host-pressure"' \
  "$root/available-memory-unavailable.json" >/dev/null
grep -F '"exitCode":72' \
  "$root/available-memory-unavailable.json" >/dev/null
grep -F '"admissionReasons":["available-memory-unavailable"]' \
  "$root/available-memory-unavailable.json" >/dev/null

env "${host_environment[@]}" \
  GERBIL_BAZEL_GUARD_FORCE_AVAILABLE_MEMORY_UNAVAILABLE=1 \
  "$gxi" "$guard" "$root/explicit-available-precedence.json" \
  explicit-available-precedence 5 \
  /bin/sh -c 'exit 0'
grep -F '"availableMemoryBytes":4294967296' \
  "$root/explicit-available-precedence.json" >/dev/null
grep -F '"admissionOutcome":"ready"' \
  "$root/explicit-available-precedence.json" >/dev/null
grep -F '"outcome":"completed"' \
  "$root/explicit-available-precedence.json" >/dev/null

env -u GERBIL_BAZEL_GUARD_MAX_RSS_BYTES "${host_environment[@]}" \
  "$gxi" "$guard" "$root/adaptive-omitted.json" adaptive-omitted 5 \
  /bin/sh -c 'exit 0'
grep -F '"maxRssBytes":3489660928' \
  "$root/adaptive-omitted.json" >/dev/null

env "${host_environment[@]}" \
  GERBIL_BAZEL_GUARD_MAX_RSS_BYTES=0 \
  "$gxi" "$guard" "$root/adaptive-zero.json" adaptive-zero 5 \
  /bin/sh -c 'exit 0'
grep -F '"maxRssBytes":3489660928' \
  "$root/adaptive-zero.json" >/dev/null

env "${common_environment[@]}" \
  "$gxi" "$guard" "$root/explicit-within-budget.json" \
  explicit-within-budget 5 \
  /bin/sh -c 'exit 0'
grep -F '"maxRssBytes":3221225472' \
  "$root/explicit-within-budget.json" >/dev/null

env "${host_environment[@]}" \
  GERBIL_BAZEL_GUARD_MAX_RSS_BYTES=4294967296 \
  "$gxi" "$guard" "$root/explicit-capped.json" explicit-capped 5 \
  /bin/sh -c 'exit 0'
grep -F '"maxRssBytes":3489660928' \
  "$root/explicit-capped.json" >/dev/null

env "${common_environment[@]}" \
  "$gxi" "$guard" "$root/completed.json" completed 5 \
  /bin/sh -c 'exit 0'
grep -F '"admissionOutcome":"ready"' "$root/completed.json" >/dev/null
grep -F '"outcome":"completed"' "$root/completed.json" >/dev/null
grep -F '"schema":"gerbil-bazel.resource-guard-receipt.v1"' \
  "$root/completed.json" >/dev/null

set +e
env \
  -u GERBIL_BAZEL_GUARD_PROCESS_TABLE_SNAPSHOT \
  -u GERBIL_BAZEL_GUARD_FORCE_PROCESS_TABLE_UNAVAILABLE \
  GERBIL_BAZEL_GUARD_SYSTEM_MEMORY_BYTES=6442450944 \
  GERBIL_BAZEL_GUARD_AVAILABLE_MEMORY_BYTES=4294967296 \
  GERBIL_BAZEL_GUARD_RSS_HEADROOM_BYTES=805306368 \
  GERBIL_BAZEL_GUARD_MAX_RSS_BYTES=1 \
  GERBIL_BAZEL_GUARD_RUNNABLE_PROCESSES=1 \
  GERBIL_BAZEL_GUARD_SAMPLE_SECONDS=0.01 \
  "$gxi" "$guard" "$root/rss-limit.json" rss-limit 0 \
  /bin/sh -c 'exec /bin/sleep 5'
rss_limit_status=$?
set -e
[[ "$rss_limit_status" -eq 70 ]]
grep -F '"outcome":"rss-limit-exceeded"' "$root/rss-limit.json" >/dev/null
grep -F '"exitCode":70' "$root/rss-limit.json" >/dev/null

set +e
env \
  GERBIL_BAZEL_GUARD_SYSTEM_MEMORY_BYTES=2147483648 \
  GERBIL_BAZEL_GUARD_AVAILABLE_MEMORY_BYTES=1073741824 \
  GERBIL_BAZEL_GUARD_RSS_HEADROOM_BYTES=536870912 \
  GERBIL_BAZEL_GUARD_MAX_RSS_BYTES=1073741824 \
  GERBIL_BAZEL_GUARD_RUNNABLE_PROCESSES=1 \
  GERBIL_BAZEL_GUARD_PROCESS_TABLE_SNAPSHOT='1 0 0' \
  "$gxi" "$guard" "$root/blocked.json" blocked 0 \
  /bin/sh -c 'exit 99'
blocked_status=$?
set -e
[[ "$blocked_status" -eq 72 ]]
grep -F '"admissionOutcome":"blocked-host-pressure"' \
  "$root/blocked.json" >/dev/null
grep -F '"admissionReasons":["insufficient-memory-headroom"]' \
  "$root/blocked.json" >/dev/null

set +e
env "${common_environment[@]}" \
  GERBIL_BAZEL_GUARD_PROCESS_TABLE_SNAPSHOT= \
  GERBIL_BAZEL_GUARD_FORCE_PROCESS_TABLE_UNAVAILABLE=1 \
  "$gxi" "$guard" "$root/unobservable.json" unobservable 0 \
  /bin/sh -c 'exit 99'
unobservable_status=$?
set -e
[[ "$unobservable_status" -eq 72 ]]
grep -F '"processTreeRssAvailable":false' "$root/unobservable.json" >/dev/null
grep -F '"admissionReasons":["process-tree-rss-unavailable"]' \
  "$root/unobservable.json" >/dev/null

set +e
env "${common_environment[@]}" \
  "$gxi" "$guard" "$root/timeout.json" timeout 1 \
  /bin/sleep 2
timeout_status=$?
set -e
[[ "$timeout_status" -eq 71 ]]
grep -F '"outcome":"timeout"' "$root/timeout.json" >/dev/null
grep -F '"timeoutMs":1000' "$root/timeout.json" >/dev/null

child_pid_file="$root/timeout-child.pid"
set +e
env "${common_environment[@]}" \
  "$gxi" "$guard" "$root/process-tree-timeout.json" process-tree-timeout 1 \
  /bin/sh -c 'sleep 30 & echo $! >"$1"; wait' guard-child "$child_pid_file"
process_tree_timeout_status=$?
set -e
[[ "$process_tree_timeout_status" -eq 71 ]]
child_pid=$(cat "$child_pid_file")
for _attempt in {1..20}; do
  child_state=$(ps -o state= -p "$child_pid" 2>/dev/null | tr -d '[:space:]' || true)
  if [[ -z "$child_state" || "$child_state" == Z* ]]; then
    break
  fi
  sleep 0.1
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
: >"$pid_file"
while :; do
  sleep 30 &
  printf '%s\n' "$!" >>"$pid_file"
  sleep 0.02
done
EOF
chmod +x "$spawner"

set +e
env "${common_environment[@]}" \
  "$gxi" "$guard" "$root/process-tree-spawner-timeout.json" \
  process-tree-spawner-timeout 1 \
  "$spawner" "$spawned_pid_file"
spawner_timeout_status=$?
set -e
[[ "$spawner_timeout_status" -eq 71 ]]
[[ -s "$spawned_pid_file" ]]

deadline=$((SECONDS + 3))
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
  sleep 0.05
done
grep -F '"outcome":"timeout"' \
  "$root/process-tree-spawner-timeout.json" >/dev/null
