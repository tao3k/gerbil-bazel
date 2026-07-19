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
