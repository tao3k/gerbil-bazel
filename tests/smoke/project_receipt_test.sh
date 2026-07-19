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

receipt=$(resolve_runfile "${1:?receipt path is required}")
log=$(resolve_runfile "${2:?log path is required}")

grep -F '"schema":"gerbil-bazel.project-receipt.v1"' "$receipt" >/dev/null
grep -F '"status":"ok"' "$receipt" >/dev/null
grep -Eq '"durationSeconds":[0-9]+' "$receipt"
grep -F '"libraryOutputRequired":false' "$receipt" >/dev/null
grep -F '"packageIdentity":""' "$receipt" >/dev/null
grep -F '"packageRevision":""' "$receipt" >/dev/null
grep -F '"buildReceipt":{"outcome":"passed","schema":"gerbil-bazel.receipt-prefix-smoke.v1"}' \
  "$receipt" >/dev/null
if grep -F '"resourceGuard"' "$receipt" >/dev/null; then
  printf 'unguarded receipt unexpectedly contains resourceGuard\n' >&2
  exit 1
fi
grep -F 'PROJECT_RECEIPT ' "$log" >/dev/null
