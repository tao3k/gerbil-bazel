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
conflict_log=$scratch/conflict.log

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
  --execution_log_json_file="$second_log" \
  //tests/smoke:compile_v2

executed_actions=$(jq -s '
  [.. | objects
   | select(.mnemonic? == "GerbilProjectCompile")
   | .targetLabel]
  | unique
' "$second_log")
expected_actions='["//tests/smoke:compile_v2","//tests/smoke:dependency_compile_v2"]'
if ! jq -en \
  --argjson actual "$executed_actions" \
  --argjson expected "$expected_actions" \
  '$actual == $expected' >/dev/null; then
  printf 'unexpected second-build Gerbil actions: %s\n' "$executed_actions" >&2
  exit 1
fi

if "$bazel_bin" --output_base="$output_base" build \
  --nobuild \
  //tests/smoke:revision_conflict >"$conflict_log" 2>&1; then
  printf 'expected conflicting immutable package revisions to fail analysis\n' >&2
  exit 1
fi
if ! grep -F \
  'depends on package example.invalid/gerbil-bazel/dependency at conflicting immutable revisions dependency-v1 and dependency-v2' \
  "$conflict_log" >/dev/null; then
  printf 'missing package revision conflict diagnostic:\n' >&2
  cat "$conflict_log" >&2
  exit 1
fi

mkdir -p "$(dirname "$receipt_path")"
jq -n \
  --arg schema gerbil-bazel.atomic-package-cache-receipt.v1 \
  --arg outcome passed \
  --arg unchanged_package example.invalid/gerbil-bazel/independent@independent-v1 \
  --arg changed_package example.invalid/gerbil-bazel/dependency@dependency-v2 \
  --argjson warm_executed_actions "$warm_executed_actions" \
  --argjson executed_actions "$executed_actions" \
  '{
    schema: $schema,
    outcome: $outcome,
    changedPackage: $changed_package,
    unchangedPackage: $unchanged_package,
    warmBuildExecutedActions: $warm_executed_actions,
    warmBuildGerbilActionCount: ($warm_executed_actions | length),
    revisionConflictRejected: true,
    secondBuildExecutedActions: $executed_actions,
    secondBuildGerbilActionCount: ($executed_actions | length)
  }' >"$receipt_path"
jq -c . "$receipt_path"
