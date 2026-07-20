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
validator=$(resolve_runfile "${2:?admission validator path is required}")
schema=$(resolve_runfile "${3:?source producer admission schema path is required}")
admission=$(resolve_runfile "${4:?source producer admission command path is required}")
receipt_dir="${TEST_TMPDIR:?TEST_TMPDIR is required}/source-producer-admission"

mkdir -p "$receipt_dir"

cache_hit_receipt="$receipt_dir/cache-hit.json"
explicit_cold_receipt="$receipt_dir/explicit-cold.json"
blocked_receipt="$receipt_dir/blocked.json"

"$admission" true "" ubuntu-latest "$cache_hit_receipt" >/dev/null
"$admission" false explicit-linux-x64-runner explicit-linux-x64-runner \
  "$explicit_cold_receipt" >/dev/null

if "$admission" false "" ubuntu-latest "$blocked_receipt" \
  >"$receipt_dir/blocked.stdout" 2>"$receipt_dir/blocked.stderr"; then
  printf '%s\n' "implicit default runner cold miss must be blocked" >&2
  exit 1
fi

"$gxi" "$validator" "$schema" \
  "$cache_hit_receipt" \
  "$explicit_cold_receipt" \
  "$blocked_receipt"
