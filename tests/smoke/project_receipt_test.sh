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

grep -Fx '{"outcome":"passed","schema":"gerbil-bazel.receipt-prefix-smoke.v1"}' \
  "$receipt" >/dev/null
grep -F 'PROJECT_RECEIPT ' "$log" >/dev/null
