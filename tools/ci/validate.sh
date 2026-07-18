#!/usr/bin/env bash
set -euo pipefail

receipt_path="${RECEIPT_PATH:-.ci/receipts/validation.json}"
phases='[]'

write_receipt() {
  local outcome="$1"
  local exit_code="$2"
  local receipt_dir
  receipt_dir="$(dirname "$receipt_path")"
  mkdir -p "$receipt_dir"
  jq -n \
    --arg schema gerbil-bazel.ci-validation-receipt.v1 \
    --arg outcome "$outcome" \
    --arg os "$(uname -s)" \
    --arg arch "$(uname -m)" \
    --arg gerbil_version "$(gxi --version)" \
    --arg bazel_version "$(bazel --version)" \
    --argjson exit_code "$exit_code" \
    --argjson phases "$phases" \
    '{
      schema: $schema,
      outcome: $outcome,
      os: $os,
      arch: $arch,
      gerbil_version: $gerbil_version,
      bazel_version: $bazel_version,
      exit_code: $exit_code,
      phases: $phases
    }' >"$receipt_path"
}

run_phase() {
  local name="$1"
  shift
  local started_at="$SECONDS"
  local exit_code
  set +e
  "$@"
  exit_code="$?"
  set -e
  phases="$(
    jq -cn \
      --argjson phases "$phases" \
      --arg name "$name" \
      --argjson exit_code "$exit_code" \
      --argjson elapsed_seconds "$((SECONDS - started_at))" \
      '$phases + [{name: $name, exit_code: $exit_code, elapsed_seconds: $elapsed_seconds}]'
  )"
  if [[ "$exit_code" -ne 0 ]]; then
    write_receipt failed "$exit_code"
    return "$exit_code"
  fi
}

run_phase query bazel query //...
run_phase build bazel build //tests/smoke:compile
run_phase test bazel test //tests/smoke:test --test_output=errors
run_phase dev bazel run //tests/smoke:dev
write_receipt passed 0
jq -c . "$receipt_path"
