#!/usr/bin/env bash
set -euo pipefail

resolve_runfile() {
  local key=$1
  local runfiles_dir=${RUNFILES_DIR:-${BASH_SOURCE[0]}.runfiles}
  local runfiles_manifest=${RUNFILES_MANIFEST_FILE:-${BASH_SOURCE[0]}.runfiles_manifest}
  local manifest_key
  local manifest_path
  if [[ -e "$key" ]]; then
    printf '%s\n' "$key"
    return 0
  fi
  if [[ -e "$runfiles_dir/$key" ]]; then
    printf '%s\n' "$runfiles_dir/$key"
    return 0
  fi
  if [[ -f "$runfiles_manifest" ]]; then
    while IFS=' ' read -r manifest_key manifest_path; do
      if [[ "$manifest_key" == "$key" ]]; then
        printf '%s\n' "$manifest_path"
        return 0
      fi
    done < "$runfiles_manifest"
  fi
  printf 'cannot resolve lifecycle runfile: %s\n' "$key" >&2
  return 1
}

success_launcher=$(resolve_runfile "$1")
failure_launcher=$(resolve_runfile "$2")
blocking_launcher=$(resolve_runfile "$3")

assert_gone() {
  local pid=$1
  if kill -0 "$pid" 2>/dev/null; then
    printf 'process %s remains alive after launcher completion\n' "$pid" >&2
    return 1
  fi
}

assert_status() {
  local name=$1
  local expected=$2
  local actual=$3
  if [[ "$actual" -ne "$expected" ]]; then
    printf '%s status mismatch: expected %s, got %s\n' \
      "$name" "$expected" "$actual" >&2
    return 1
  fi
}

wait_for_terminal_replacement() {
  local pid=$1
  local launcher=$2
  local log=$3
  local attempt
  local command
  local settle
  local status
  for attempt in $(seq 1 100); do
    if ! kill -0 "$pid" 2>/dev/null; then
      set +e
      wait "$pid"
      status=$?
      set -e
      printf 'launcher %s exited with status %s before lifecycle observation\n' \
        "$launcher" "$status" >&2
      if [[ -s "$log" ]]; then
        printf '%s\n' '--- launcher log ---' >&2
        cat "$log" >&2
      fi
      return 1
    fi
    command=$(ps -p "$pid" -o command=)
    if [[ "$command" != *"$launcher"* ]]; then
      for settle in $(seq 1 100); do
        if ! pgrep -P "$pid" >/dev/null 2>&1; then
          return 0
        fi
        sleep 0.02
      done
      printf 'terminal gxtest process %s retains child processes\n' "$pid" >&2
      return 1
    fi
    sleep 0.05
  done
  printf 'launcher %s did not terminally exec gxtest\n' "$launcher" >&2
  return 1
}

set +e
"$success_launcher" >/dev/null 2>&1 &
success_pid=$!
wait "$success_pid"
success_status=$?
set -e
assert_status success 0 "$success_status"
assert_gone "$success_pid"

set +e
"$failure_launcher" >/dev/null 2>&1 &
failure_pid=$!
wait "$failure_pid"
failure_status=$?
set -e
if [[ "$failure_status" -eq 0 ]]; then
  printf 'failure launcher unexpectedly returned success\n' >&2
  exit 1
fi
assert_gone "$failure_pid"

set +e
cancel_log="${TEST_TMPDIR:-/tmp}/gerbil-test-cancel.log"
"$blocking_launcher" >"$cancel_log" 2>&1 &
cancel_pid=$!
set -e
wait_for_terminal_replacement "$cancel_pid" "$blocking_launcher" "$cancel_log"
kill -TERM "$cancel_pid"
set +e
wait "$cancel_pid"
cancel_status=$?
set -e
if [[ "$cancel_status" -eq 0 ]]; then
  printf 'cancelled launcher unexpectedly returned success\n' >&2
  exit 1
fi
assert_gone "$cancel_pid"

set +e
timeout_log="${TEST_TMPDIR:-/tmp}/gerbil-test-timeout.log"
"$blocking_launcher" >"$timeout_log" 2>&1 &
timeout_pid=$!
set -e
wait_for_terminal_replacement "$timeout_pid" "$blocking_launcher" "$timeout_log"
kill -KILL "$timeout_pid"
set +e
wait "$timeout_pid"
timeout_status=$?
set -e
assert_status timeout 137 "$timeout_status"
assert_gone "$timeout_pid"

printf '%s\n' \
  "GERBIL_TEST_LIFECYCLE_RECEIPT {\"schema\":\"gerbil-bazel.test-lifecycle-receipt.v1\",\"launcherReplaced\":true,\"childProcesses\":0,\"successStatus\":$success_status,\"failureStatus\":$failure_status,\"cancelStatus\":$cancel_status,\"timeoutStatus\":$timeout_status}"
