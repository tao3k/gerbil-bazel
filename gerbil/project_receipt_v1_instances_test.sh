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
schema=$(resolve_runfile "${3:?project receipt schema path is required}")
no_prefix_receipt=$(resolve_runfile "${4:?no-prefix receipt path is required}")
prefix_receipt=$(resolve_runfile "${5:?prefix receipt path is required}")
guarded_receipt=$(resolve_runfile "${6:?guarded receipt path is required}")

"$gxi" "$validator" "$schema" \
  "$no_prefix_receipt" \
  "$prefix_receipt" \
  "$guarded_receipt"

write_project_receipt() {
  local path=$1
  local resource_budget=$2
  printf '%s\n' \
    '{"schema":"gerbil-bazel.project-receipt.v1","status":"ok","durationSeconds":0,"libraryOutputRequired":false,"packageIdentity":"test","packageRevision":"test","resourceBudget":'"$resource_budget"'}' \
    >"$path"
}

missing_budget="${TEST_TMPDIR:?TEST_TMPDIR is required}/missing-resource-budget.json"
unknown_budget_field="$TEST_TMPDIR/unknown-resource-budget-field.json"
zero_positive_budget_field="$TEST_TMPDIR/zero-positive-resource-budget-field.json"
invalid_budget_decision="$TEST_TMPDIR/invalid-resource-budget-decision.json"
negative_available_memory="$TEST_TMPDIR/negative-resource-budget-available-memory.json"

printf '%s\n' \
  '{"schema":"gerbil-bazel.project-receipt.v1","status":"ok","durationSeconds":0,"libraryOutputRequired":false,"packageIdentity":"test","packageRevision":"test"}' \
  >"$missing_budget"
write_project_receipt "$unknown_budget_field" \
  '{"schema":"gerbil-bazel.resource-budget.v1","decision":"adaptive-configured","selectedCores":1,"requestedCores":1,"configuredCores":1,"logicalCpuCount":1,"memoryPerCoreBytes":1,"memoryCoreLimit":1,"availableMemoryBytes":0,"maxRssBytes":1,"unknown":true}'
write_project_receipt "$zero_positive_budget_field" \
  '{"schema":"gerbil-bazel.resource-budget.v1","decision":"adaptive-configured","selectedCores":0,"requestedCores":1,"configuredCores":1,"logicalCpuCount":1,"memoryPerCoreBytes":1,"memoryCoreLimit":1,"availableMemoryBytes":0,"maxRssBytes":1}'
write_project_receipt "$invalid_budget_decision" \
  '{"schema":"gerbil-bazel.resource-budget.v1","decision":"fixed","selectedCores":1,"requestedCores":1,"configuredCores":1,"logicalCpuCount":1,"memoryPerCoreBytes":1,"memoryCoreLimit":1,"availableMemoryBytes":0,"maxRssBytes":1}'
write_project_receipt "$negative_available_memory" \
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
    printf 'expected invalid project receipt to fail: %s\n' "$receipt" >&2
    exit 1
  fi
done
