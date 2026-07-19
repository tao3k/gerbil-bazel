#!/usr/bin/env bash
set -euo pipefail

bazel_bin=${BAZEL:-bazelisk}
receipt_path=${ATOMIC_RECEIPT_PATH:-.ci/receipts/atomic-package-cache.json}
scratch=$(mktemp -d "${TMPDIR:-/tmp}/gerbil-bazel-atomic.XXXXXX")

output_base=$scratch/output-base
disk_cache=$scratch/disk-cache
first_log=$scratch/first.json
warm_log=$scratch/warm.json
second_log=$scratch/second.json

cleanup() {
  "$bazel_bin" --output_base="$output_base" shutdown >/dev/null 2>&1 || true
  chmod -R u+w "$scratch" 2>/dev/null || true
  rm -rf "$scratch"
}
trap cleanup EXIT

"$bazel_bin" --output_base="$output_base" build \
  --disk_cache="$disk_cache" \
  --execution_log_json_file="$first_log" \
  //tests/smoke:compile
"$bazel_bin" --output_base="$output_base" build \
  --disk_cache="$disk_cache" \
  --execution_log_json_file="$warm_log" \
  //tests/smoke:compile

warm_executed_actions=$(jq -s '
  [.. | objects
   | select(.mnemonic? == "GerbilProjectCompile")
   | .targetLabel]
  | unique
' "$warm_log")
if ! jq -en --argjson actual "$warm_executed_actions" '$actual == []' >/dev/null; then
  printf 'unexpected warm-build Gerbil actions: %s\n' "$warm_executed_actions" >&2
  exit 1
fi

"$bazel_bin" --output_base="$output_base" build \
  --disk_cache="$disk_cache" \
  --//tests/smoke:dependency_state=changed \
  --execution_log_json_file="$second_log" \
  //tests/smoke:compile

executed_actions=$(jq -s '
  [.. | objects
   | select(.mnemonic? == "GerbilProjectCompile")
   | .targetLabel]
  | unique
' "$second_log")
expected_actions='["//tests/smoke:compile","//tests/smoke:dependency_compile"]'
if ! jq -en \
  --argjson actual "$executed_actions" \
  --argjson expected "$expected_actions" \
  '$actual == $expected' >/dev/null; then
  printf 'unexpected second-build Gerbil actions: %s\n' "$executed_actions" >&2
  exit 1
fi

mkdir -p "$(dirname "$receipt_path")"
jq -n \
  --arg schema gerbil-bazel.atomic-package-cache-receipt.v1 \
  --arg outcome passed \
  --arg changed_input //tests/smoke:dependency-changed.ss \
  --arg unchanged_dependency //tests/smoke:independent_compile \
  --argjson warm_executed_actions "$warm_executed_actions" \
  --argjson executed_actions "$executed_actions" \
  '{
    schema: $schema,
    outcome: $outcome,
    changedInput: $changed_input,
    unchangedDependency: $unchanged_dependency,
    warmBuildExecutedActions: $warm_executed_actions,
    warmBuildGerbilActionCount: ($warm_executed_actions | length),
    declaredInputInvalidationVerified: true,
    secondBuildExecutedActions: $executed_actions,
    secondBuildGerbilActionCount: ($executed_actions | length)
  }' >"$receipt_path"
jq -c . "$receipt_path"
