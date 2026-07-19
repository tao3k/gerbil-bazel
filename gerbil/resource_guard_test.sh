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

common_environment=(
  GERBIL_BAZEL_GUARD_SYSTEM_MEMORY_BYTES=17179869184
  GERBIL_BAZEL_GUARD_AVAILABLE_MEMORY_BYTES=12884901888
  GERBIL_BAZEL_GUARD_RSS_HEADROOM_BYTES=1073741824
  GERBIL_BAZEL_GUARD_MAX_RSS_BYTES=8589934592
  GERBIL_BAZEL_GUARD_RUNNABLE_PROCESSES=1
  GERBIL_BAZEL_GUARD_SAMPLE_SECONDS=0.05
  "GERBIL_BAZEL_GUARD_PROCESS_TABLE_SNAPSHOT=1 0 0"
)

env "${common_environment[@]}" \
  "$gxi" "$guard" "$root/completed.json" completed 5 \
  /bin/sh -c 'exit 0'
grep -F '"admissionOutcome":"ready"' "$root/completed.json" >/dev/null
grep -F '"outcome":"completed"' "$root/completed.json" >/dev/null
grep -F '"schema":"gerbil-bazel.resource-guard-receipt.v1"' \
  "$root/completed.json" >/dev/null

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
  "$gxi" "$guard" "$root/timeout.json" timeout 1 \
  /bin/sleep 2
timeout_status=$?
set -e
[[ "$timeout_status" -eq 71 ]]
grep -F '"outcome":"timeout"' "$root/timeout.json" >/dev/null
grep -F '"timeoutMs":1000' "$root/timeout.json" >/dev/null
