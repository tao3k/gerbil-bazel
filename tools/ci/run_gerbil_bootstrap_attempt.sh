#!/usr/bin/env bash
set -euo pipefail

if (( $# < 5 )); then
  printf '%s\n' \
    "usage: run_gerbil_bootstrap_attempt.sh TIMEOUT_MINUTES TERMINATION_GRACE_SECONDS IDENTITY_RECEIPT ATTEMPT_RECEIPT COMMAND [ARG ...]" \
    >&2
  exit 64
fi

timeout_minutes=$1
termination_grace_seconds=$2
identity_receipt=$3
attempt_receipt=$4
shift 4

if [[ ! "$timeout_minutes" =~ ^[1-9][0-9]*$ || "$timeout_minutes" -gt 360 ]]; then
  printf 'invalid bootstrap timeout minutes: %s\n' "$timeout_minutes" >&2
  exit 64
fi
if [[ ! "$termination_grace_seconds" =~ ^[1-9][0-9]*$ ||
      "$termination_grace_seconds" -gt 300 ]]; then
  printf 'invalid bootstrap termination grace seconds: %s\n' \
    "$termination_grace_seconds" >&2
  exit 64
fi

if ! identity_json="$(
  jq -cSe \
    --argjson timeout_minutes "$timeout_minutes" \
    --argjson termination_grace_seconds "$termination_grace_seconds" \
    'select(.schema == "gerbil-bazel.source-build-identity.v1") |
     select(.installDigest | test("^[0-9a-f]{64}$")) |
     select(.config.digest | test("^[0-9a-f]{64}$")) |
     select(.config.value.executionPolicy.buildTimeoutMinutes == $timeout_minutes) |
     select(.config.value.executionPolicy.terminationGraceSeconds == $termination_grace_seconds)' \
    "$identity_receipt"
)"; then
  printf 'source build identity does not authorize bootstrap attempt policy\n' >&2
  exit 65
fi

install_digest="$(jq -er '.installDigest' <<<"$identity_json")"
config_digest="$(jq -er '.config.digest' <<<"$identity_json")"
attempt_dir="$(dirname "$attempt_receipt")"
attempt_name="$(basename "$attempt_receipt")"
progress_receipt="$attempt_dir/.$attempt_name.progress"
success_receipt="${GERBIL_PREFIX:?GERBIL_PREFIX is required}/bootstrap.receipt.json"
started_at=$SECONDS
timeout_pid=
received_signal=
default_checkpoint_snapshot='{
  "restoreOutcome": "not-observed",
  "restoredBoundary": false,
  "restoredBoundaryIndex": false,
  "restoredGeneration": false,
  "lastSafeBoundary": false,
  "lastSafeBoundaryIndex": false
}'

read_last_phase() {
  if [[ -f "$progress_receipt" ]]; then
    jq -er '.phase | select(type == "string" and length > 0)' \
      "$progress_receipt" 2>/dev/null || true
  fi
}

read_checkpoint_snapshot() {
  local checkpoint_json=
  if [[ -f "$progress_receipt" ]]; then
    checkpoint_json="$(
      jq -cSe '
        def valid_boundary_index($boundary; $index):
          ($boundary == false and $index == false) or
          ($boundary == "stage1" and $index == 4) or
          ($boundary == "stdlib" and $index == 5) or
          ($boundary == "tools" and $index == 10);
        .checkpoint |
        . as $checkpoint |
        select((keys | sort) == ([
          "lastSafeBoundary",
          "lastSafeBoundaryIndex",
          "restoreOutcome",
          "restoredBoundary",
          "restoredBoundaryIndex",
          "restoredGeneration"
        ] | sort)) |
        select([
          "not-observed",
          "not-configured",
          "not-found",
          "pending",
          "rejected",
          "restored"
        ] | index($checkpoint.restoreOutcome) != null) |
        select(valid_boundary_index(
          $checkpoint.restoredBoundary;
          $checkpoint.restoredBoundaryIndex
        )) |
        select(valid_boundary_index(
          $checkpoint.lastSafeBoundary;
          $checkpoint.lastSafeBoundaryIndex
        )) |
        select(
          if ["not-observed", "not-configured", "pending"] |
               index($checkpoint.restoreOutcome) != null then
            $checkpoint.lastSafeBoundary == false and
            $checkpoint.lastSafeBoundaryIndex == false
          else
            true
          end
        ) |
        select(
          if $checkpoint.restoreOutcome == "restored" then
            $checkpoint.restoredBoundary != false and
            (
              ($checkpoint.restoredBoundary == "stage1" and
                ($checkpoint.restoredGeneration |
                  type == "string" and
                  test("^generation-stage1-[0-9]+-[0-9]+$"))) or
              ($checkpoint.restoredBoundary == "stdlib" and
                ($checkpoint.restoredGeneration |
                  type == "string" and
                  test("^generation-stdlib-[0-9]+-[0-9]+$"))) or
              ($checkpoint.restoredBoundary == "tools" and
                ($checkpoint.restoredGeneration |
                  type == "string" and
                  test("^generation-tools-[0-9]+-[0-9]+$")))
            ) and
            $checkpoint.lastSafeBoundary != false and
            $checkpoint.lastSafeBoundaryIndex >=
              $checkpoint.restoredBoundaryIndex
          else
            $checkpoint.restoredBoundary == false and
            $checkpoint.restoredBoundaryIndex == false and
            $checkpoint.restoredGeneration == false
          end
        )
      ' "$progress_receipt" 2>/dev/null || true
    )"
  fi
  if [[ -n "$checkpoint_json" ]]; then
    printf '%s\n' "$checkpoint_json"
  else
    printf '%s\n' "$default_checkpoint_snapshot"
  fi
}

write_attempt_receipt() {
  local outcome=$1
  local exit_code=$2
  local signal_name=$3
  local success_receipt_present=$4
  local success_receipt_validated=$5
  local last_phase
  local checkpoint_json
  local last_phase_known=false
  local signal_known=false
  local attempt_tmp

  last_phase="$(read_last_phase)"
  checkpoint_json="$(read_checkpoint_snapshot)"
  case "$last_phase" in
    source-prepare | configure | upstream-build | install) last_phase_known=true ;;
    *) last_phase= ;;
  esac
  if [[ -n "$signal_name" ]]; then
    signal_known=true
  fi

  mkdir -p "$attempt_dir"
  attempt_tmp="$(mktemp "$attempt_dir/.$attempt_name.tmp.XXXXXX")"
  if ! jq -n \
    --arg schema gerbil-bazel.gerbil-bootstrap-attempt.v2 \
    --arg outcome "$outcome" \
    --arg install_digest "$install_digest" \
    --arg config_digest "$config_digest" \
    --argjson timeout_minutes "$timeout_minutes" \
    --argjson termination_grace_seconds "$termination_grace_seconds" \
    --argjson elapsed_seconds "$((SECONDS - started_at))" \
    --arg last_phase "$last_phase" \
    --argjson last_phase_known "$last_phase_known" \
    --argjson exit_code "$exit_code" \
    --arg signal_name "$signal_name" \
    --argjson signal_known "$signal_known" \
    --argjson success_receipt_present "$success_receipt_present" \
    --argjson success_receipt_validated "$success_receipt_validated" \
    --argjson checkpoint "$checkpoint_json" \
    '{
      schema: $schema,
      outcome: $outcome,
      installDigest: $install_digest,
      configDigest: $config_digest,
      timeoutMinutes: $timeout_minutes,
      terminationGraceSeconds: $termination_grace_seconds,
      elapsedSeconds: $elapsed_seconds,
      lastPhase: (if $last_phase_known then $last_phase else false end),
      exitCode: $exit_code,
      signal: (if $signal_known then $signal_name else false end),
      successReceiptPresent: $success_receipt_present,
      successReceiptValidated: $success_receipt_validated,
      checkpoint: $checkpoint
    }' >"$attempt_tmp"; then
    rm -f "$attempt_tmp"
    return 1
  fi
  mv "$attempt_tmp" "$attempt_receipt"
  jq -c . "$attempt_receipt"
}

forward_signal() {
  local signal_name=$1
  received_signal=$signal_name
  if [[ -n "$timeout_pid" ]] && kill -0 "$timeout_pid" 2>/dev/null; then
    kill -s "$signal_name" "$timeout_pid" 2>/dev/null || true
  fi
}

trap 'forward_signal TERM' TERM
trap 'forward_signal INT' INT

mkdir -p "$attempt_dir"
rm -f "$progress_receipt"
if [[ -f "$success_receipt" ]]; then
  write_attempt_receipt failed 66 "" true false
  printf 'bootstrap attempt refused a pre-existing immutable success receipt: %s\n' \
    "$success_receipt" >&2
  exit 66
fi
timeout_executable="$(command -v timeout || true)"
if [[ -z "$timeout_executable" ]]; then
  write_attempt_receipt failed 69 "" false false
  printf 'GNU timeout is required for the source-build guard\n' >&2
  exit 69
fi

set +e
GERBIL_BOOTSTRAP_PROGRESS_RECEIPT="$progress_receipt" \
  GERBIL_EXPECTED_INSTALL_DIGEST="$install_digest" \
  "$timeout_executable" \
    --signal=TERM \
    --kill-after="${termination_grace_seconds}s" \
    "${timeout_minutes}m" \
    "$@" &
timeout_pid=$!
wait "$timeout_pid"
child_status=$?
set -e

trap - TERM INT

success_receipt_present=false
success_receipt_validated=false
if [[ -f "$success_receipt" ]]; then
  success_receipt_present=true
  if [[ "$child_status" -eq 0 ]] && jq -e \
    --arg install_digest "$install_digest" \
    '.schema == "gerbil-bazel.gerbil-bootstrap-receipt.v1" and
     .outcome == "ready" and
     .source_build_identity.installDigest == $install_digest' \
    "$success_receipt" >/dev/null; then
    success_receipt_validated=true
  fi
fi

outcome=failed
exit_code=$child_status
signal_name=
final_status=$child_status
if [[ -n "$received_signal" ]]; then
  outcome=interrupted
  exit_code=false
  signal_name=$received_signal
  case "$received_signal" in
    INT) final_status=130 ;;
    TERM) final_status=143 ;;
  esac
elif [[ "$child_status" -eq 124 ]]; then
  outcome=timed-out
  exit_code=false
  signal_name=TERM
elif [[ "$child_status" -eq 130 || "$child_status" -eq 143 ]]; then
  outcome=interrupted
  exit_code=false
  if [[ "$child_status" -eq 130 ]]; then
    signal_name=INT
  else
    signal_name=TERM
  fi
elif [[ "$child_status" -eq 0 && "$success_receipt_validated" == true ]]; then
  outcome=ready
  exit_code=0
elif [[ "$child_status" -eq 0 ]]; then
  outcome=failed
  exit_code=70
  final_status=70
fi

write_attempt_receipt \
  "$outcome" \
  "$exit_code" \
  "$signal_name" \
  "$success_receipt_present" \
  "$success_receipt_validated"

exit "$final_status"
