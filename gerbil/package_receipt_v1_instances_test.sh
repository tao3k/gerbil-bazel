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
validator=$(resolve_runfile "${2:?receipt validator path is required}")
schema=$(resolve_runfile "${3:?package receipt schema path is required}")
shift 3
if (($# == 0)); then
  echo "at least one package receipt path is required" >&2
  exit 1
fi
receipts=()
for receipt in "$@"; do
  receipts+=("$(resolve_runfile "$receipt")")
done

"$gxi" "$validator" "$schema" "${receipts[@]}"

write_package_receipt() {
  local path=$1
  local resource_budget=$2
  printf '%s\n' \
    '{"schema":"gerbil-bazel.package-receipt.v1","status":"ok","durationSeconds":0,"libraryOutputRequired":false,"packageIdentity":"test","packageReference":"test","packageRevision":"test","resourceBudget":'"$resource_budget"'}' \
    >"$path"
}

missing_budget="${TEST_TMPDIR:?TEST_TMPDIR is required}/missing-resource-budget.json"
unknown_budget_field="$TEST_TMPDIR/unknown-resource-budget-field.json"
zero_positive_budget_field="$TEST_TMPDIR/zero-positive-resource-budget-field.json"
invalid_budget_decision="$TEST_TMPDIR/invalid-resource-budget-decision.json"
negative_available_memory="$TEST_TMPDIR/negative-resource-budget-available-memory.json"

printf '%s\n' \
  '{"schema":"gerbil-bazel.package-receipt.v1","status":"ok","durationSeconds":0,"libraryOutputRequired":false,"packageIdentity":"test","packageReference":"test","packageRevision":"test"}' \
  >"$missing_budget"
write_package_receipt "$unknown_budget_field" \
  '{"schema":"gerbil-bazel.resource-budget.v1","decision":"adaptive-configured","selectedCores":1,"requestedCores":1,"configuredCores":1,"logicalCpuCount":1,"memoryPerCoreBytes":1,"memoryCoreLimit":1,"availableMemoryBytes":0,"maxRssBytes":1,"unknown":true}'
write_package_receipt "$zero_positive_budget_field" \
  '{"schema":"gerbil-bazel.resource-budget.v1","decision":"adaptive-configured","selectedCores":0,"requestedCores":1,"configuredCores":1,"logicalCpuCount":1,"memoryPerCoreBytes":1,"memoryCoreLimit":1,"availableMemoryBytes":0,"maxRssBytes":1}'
write_package_receipt "$invalid_budget_decision" \
  '{"schema":"gerbil-bazel.resource-budget.v1","decision":"fixed","selectedCores":1,"requestedCores":1,"configuredCores":1,"logicalCpuCount":1,"memoryPerCoreBytes":1,"memoryCoreLimit":1,"availableMemoryBytes":0,"maxRssBytes":1}'
write_package_receipt "$negative_available_memory" \
  '{"schema":"gerbil-bazel.resource-budget.v1","decision":"adaptive-configured","selectedCores":1,"requestedCores":1,"configuredCores":1,"logicalCpuCount":1,"memoryPerCoreBytes":1,"memoryCoreLimit":1,"availableMemoryBytes":-1,"maxRssBytes":1}'

invalid_receipts=(
  "$missing_budget"
  "$unknown_budget_field"
  "$zero_positive_budget_field"
  "$invalid_budget_decision"
  "$negative_available_memory"
)
for receipt in "${invalid_receipts[@]}"; do
  set +e
  "$gxi" "$validator" "$schema" "$receipt" >/dev/null 2>&1
  status=$?
  set -e
  if [[ $status -eq 0 ]]; then
    printf 'expected invalid package receipt to fail: %s\n' "$receipt" >&2
    exit 1
  fi
done
