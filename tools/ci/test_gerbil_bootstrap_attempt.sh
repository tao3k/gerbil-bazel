#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
test_root="$(mktemp -d)"
trap 'rm -rf "$test_root"' EXIT
mkdir -p "$test_root/bin" "$test_root/receipts"

identity_receipt="$test_root/source-build-identity.json"
schema="$repo_root/schemas/gerbil-bazel.gerbil-bootstrap-attempt.v1.schema.json"
install_digest="$(printf 'a%.0s' {1..64})"
config_digest="$(printf 'b%.0s' {1..64})"

jq -n \
  --arg install_digest "$install_digest" \
  --arg config_digest "$config_digest" \
  '{
    schema: "gerbil-bazel.source-build-identity.v1",
    installDigest: $install_digest,
    config: {
      digest: $config_digest,
      value: {
        executionPolicy: {
          buildTimeoutMinutes: 12,
          terminationGraceSeconds: 30
        }
      }
    }
  }' >"$identity_receipt"

cat >"$test_root/bin/timeout" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
while [[ "${1:-}" == --* ]]; do
  shift
done
: "${1:?timeout duration is required}"
shift

write_progress() {
  local phase=$1
  mkdir -p "$(dirname "${GERBIL_BOOTSTRAP_PROGRESS_RECEIPT:?}")"
  jq -n --arg phase "$phase" \
    '{phase: $phase, state: "running", exit_code: false}' \
    >"$GERBIL_BOOTSTRAP_PROGRESS_RECEIPT"
}

case "${BOOTSTRAP_ATTEMPT_TIMEOUT_MODE:-exec}" in
  exec)
    exec "$@"
    ;;
  timed-out)
    write_progress upstream-build
    exit 124
    ;;
  wait-term)
    write_progress configure
    trap 'exit 143' TERM
    while :; do
      sleep 1
    done
    ;;
  *)
    exit 64
    ;;
esac
EOF

cat >"$test_root/bin/bootstrap-child" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

write_progress() {
  local phase=$1
  mkdir -p "$(dirname "${GERBIL_BOOTSTRAP_PROGRESS_RECEIPT:?}")"
  jq -n --arg phase "$phase" \
    '{phase: $phase, state: "completed", exit_code: 0}' \
    >"$GERBIL_BOOTSTRAP_PROGRESS_RECEIPT"
}

case "${SYNTHETIC_BOOTSTRAP_MODE:-ready}" in
  ready)
    write_progress install
    mkdir -p "$GERBIL_PREFIX"
    jq -n \
      --arg install_digest "${GERBIL_EXPECTED_INSTALL_DIGEST:?}" \
      '{
        schema: "gerbil-bazel.gerbil-bootstrap-receipt.v1",
        outcome: "ready",
        source_build_identity: {installDigest: $install_digest}
      }' \
      >"$GERBIL_PREFIX/bootstrap.receipt.json"
    ;;
  failed)
    write_progress upstream-build
    exit 42
    ;;
  missing-success-receipt)
    write_progress install
    ;;
  invalid-success-receipt)
    write_progress install
    mkdir -p "$GERBIL_PREFIX"
    jq -n '{schema: "invalid", outcome: "ready"}' \
      >"$GERBIL_PREFIX/bootstrap.receipt.json"
    ;;
  *)
    exit 64
    ;;
esac
EOF

chmod +x "$test_root/bin/bootstrap-child" "$test_root/bin/timeout"

jq -e '
  .properties.schema.const == "gerbil-bazel.gerbil-bootstrap-attempt.v1" and
  .additionalProperties == false and
  .properties.outcome.enum == ["ready", "failed", "timed-out", "interrupted"] and
  (.required | length) == 12 and
  (.allOf | length) == 4 and
  .allOf[0].if.properties.outcome.const == "ready" and
  .allOf[0].then.properties.successReceiptPresent.const == true and
  .allOf[0].then.properties.successReceiptValidated.const == true and
  .allOf[1].if.properties.outcome.const == "failed" and
  .allOf[1].then.properties.exitCode.minimum == 1 and
  .allOf[2].if.properties.outcome.const == "timed-out" and
  .allOf[2].then.properties.signal.const == "TERM" and
  .allOf[3].if.properties.outcome.const == "interrupted" and
  .allOf[3].then.properties.exitCode.const == false
' "$schema" >/dev/null

assert_receipt() {
  local receipt=$1
  local expected_outcome=$2
  local expected_exit_code=$3
  local expected_signal=$4
  local expected_success=$5
  local expected_validated=$6
  local expected_phase=$7
  jq -e \
    --arg outcome "$expected_outcome" \
    --argjson exit_code "$expected_exit_code" \
    --arg signal "$expected_signal" \
    --argjson success "$expected_success" \
    --argjson validated "$expected_validated" \
    --arg phase "$expected_phase" \
    --arg install_digest "$install_digest" \
    --arg config_digest "$config_digest" \
    '.schema == "gerbil-bazel.gerbil-bootstrap-attempt.v1" and
     .outcome == $outcome and
     .installDigest == $install_digest and
     .configDigest == $config_digest and
     .timeoutMinutes == 12 and
     .terminationGraceSeconds == 30 and
     (.elapsedSeconds | type) == "number" and
     .exitCode == $exit_code and
     .signal == (if $signal == "false" then false else $signal end) and
     .successReceiptPresent == $success and
     .successReceiptValidated == $validated and
     .lastPhase == (if $phase == "false" then false else $phase end) and
     (keys | sort) == ([
       "configDigest",
       "elapsedSeconds",
       "exitCode",
       "installDigest",
       "lastPhase",
       "outcome",
       "schema",
       "signal",
       "successReceiptPresent",
       "successReceiptValidated",
       "terminationGraceSeconds",
       "timeoutMinutes"
     ] | sort)' \
    "$receipt" >/dev/null
}

run_case() {
  local name=$1
  local timeout_mode=$2
  local bootstrap_mode=$3
  local expected_status=$4
  local expected_outcome=$5
  local expected_exit_code=$6
  local expected_signal=$7
  local expected_success=$8
  local expected_validated=$9
  local expected_phase=${10}
  local prefix="$test_root/prefix-$name"
  local receipt="$test_root/receipts/$name.json"
  local observed_status

  set +e
  PATH="$test_root/bin:$PATH" \
    BOOTSTRAP_ATTEMPT_TIMEOUT_MODE="$timeout_mode" \
    SYNTHETIC_BOOTSTRAP_MODE="$bootstrap_mode" \
    GERBIL_PREFIX="$prefix" \
    "$repo_root/tools/ci/run_gerbil_bootstrap_attempt.sh" \
      12 \
      30 \
      "$identity_receipt" \
      "$receipt" \
      "$test_root/bin/bootstrap-child" >/dev/null
  observed_status=$?
  set -e

  if [[ "$observed_status" -ne "$expected_status" ]]; then
    printf 'unexpected %s status: expected %s, observed %s\n' \
      "$name" "$expected_status" "$observed_status" >&2
    exit 1
  fi
  assert_receipt \
    "$receipt" \
    "$expected_outcome" \
    "$expected_exit_code" \
    "$expected_signal" \
    "$expected_success" \
    "$expected_validated" \
    "$expected_phase"
}

run_case ready exec ready 0 ready 0 false true true install
run_case failed exec failed 42 failed 42 false false false upstream-build
run_case timed-out timed-out ready 124 timed-out false TERM false false upstream-build
run_case missing-success exec missing-success-receipt 70 failed 70 false false false install
run_case invalid-success exec invalid-success-receipt 70 failed 70 false true false install

stale_prefix="$test_root/prefix-stale"
stale_receipt="$test_root/receipts/stale.json"
mkdir -p "$stale_prefix"
jq -n \
  --arg install_digest "$install_digest" \
  '{
    schema: "gerbil-bazel.gerbil-bootstrap-receipt.v1",
    outcome: "ready",
    source_build_identity: {installDigest: $install_digest}
  }' >"$stale_prefix/bootstrap.receipt.json"
set +e
PATH="$test_root/bin:$PATH" \
  GERBIL_PREFIX="$stale_prefix" \
  "$repo_root/tools/ci/run_gerbil_bootstrap_attempt.sh" \
    12 \
    30 \
    "$identity_receipt" \
    "$stale_receipt" \
    "$test_root/bin/bootstrap-child" >/dev/null 2>&1
stale_status=$?
set -e
if [[ "$stale_status" -ne 66 ]]; then
  printf 'bootstrap attempt accepted a pre-existing success receipt: %s\n' \
    "$stale_status" >&2
  exit 1
fi
assert_receipt "$stale_receipt" failed 66 false true false false

term_prefix="$test_root/prefix-interrupted"
term_receipt="$test_root/receipts/interrupted.json"
PATH="$test_root/bin:$PATH" \
  BOOTSTRAP_ATTEMPT_TIMEOUT_MODE=wait-term \
  GERBIL_PREFIX="$term_prefix" \
  "$repo_root/tools/ci/run_gerbil_bootstrap_attempt.sh" \
    12 \
    30 \
    "$identity_receipt" \
    "$term_receipt" \
    "$test_root/bin/bootstrap-child" >/dev/null &
wrapper_pid=$!

for _attempt in {1..100}; do
  if [[ -f "$test_root/receipts/.interrupted.json.progress" ]]; then
    break
  fi
  sleep 0.01
done
kill -TERM "$wrapper_pid"
set +e
wait "$wrapper_pid"
term_status=$?
set -e
if [[ "$term_status" -ne 143 ]]; then
  printf 'interrupted wrapper did not preserve TERM status: %s\n' "$term_status" >&2
  exit 1
fi
assert_receipt "$term_receipt" interrupted false TERM false false configure

system_timeout="$(command -v timeout || true)"
if [[ -n "$system_timeout" ]] &&
   "$system_timeout" --version 2>/dev/null | head -n 1 | grep -F 'GNU coreutils' >/dev/null; then
  cat >"$test_root/bin/real-timeout-child" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
pid_file=${1:?descendant PID file is required}
sleep 300 &
descendant_pid=$!
printf '%s\n' "$descendant_pid" >"$pid_file"
wait "$descendant_pid"
EOF
  chmod +x "$test_root/bin/real-timeout-child"

  assert_process_gone() {
    local pid=$1
    for _attempt in {1..100}; do
      if ! kill -0 "$pid" 2>/dev/null; then
        return
      fi
      sleep 0.01
    done
    kill -KILL "$pid" 2>/dev/null || true
    printf 'GNU timeout left descendant process alive: %s\n' "$pid" >&2
    exit 1
  }

  timed_out_pid_file="$test_root/timed-out-descendant.pid"
  set +e
  "$system_timeout" \
    --signal=TERM \
    --kill-after=1s \
    1s \
    "$test_root/bin/real-timeout-child" "$timed_out_pid_file"
  real_timeout_status=$?
  set -e
  if [[ "$real_timeout_status" -ne 124 ]]; then
    printf 'GNU timeout did not preserve status 124: %s\n' \
      "$real_timeout_status" >&2
    exit 1
  fi
  if [[ ! -f "$timed_out_pid_file" ]]; then
    printf 'GNU timeout probe did not record its descendant PID\n' >&2
    exit 1
  fi
  assert_process_gone "$(<"$timed_out_pid_file")"

  interrupted_pid_file="$test_root/interrupted-descendant.pid"
  "$system_timeout" \
    --signal=TERM \
    --kill-after=1s \
    30s \
    "$test_root/bin/real-timeout-child" "$interrupted_pid_file" &
  real_timeout_pid=$!
  for _attempt in {1..100}; do
    if [[ -f "$interrupted_pid_file" ]]; then
      break
    fi
    sleep 0.01
  done
  kill -TERM "$real_timeout_pid"
  set +e
  wait "$real_timeout_pid"
  real_term_status=$?
  set -e
  if [[ "$real_term_status" -ne 143 ]]; then
    printf 'GNU timeout did not preserve external TERM status 143: %s\n' \
      "$real_term_status" >&2
    exit 1
  fi
  if [[ ! -f "$interrupted_pid_file" ]]; then
    printf 'GNU timeout TERM probe did not record its descendant PID\n' >&2
    exit 1
  fi
  assert_process_gone "$(<"$interrupted_pid_file")"
fi

shopt -s nullglob
temporary_receipts=("$test_root/receipts"/.*.tmp.*)
if (( ${#temporary_receipts[@]} != 0 )); then
  printf 'bootstrap attempt left temporary receipt files\n' >&2
  exit 1
fi
