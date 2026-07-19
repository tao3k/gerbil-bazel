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
validator=$(resolve_runfile "${2:?JSON validator path is required}")
root=${TEST_TMPDIR:?TEST_TMPDIR is required}/validate-json
mkdir -p "$root"

printf '{"outcome":"passed","schema":"test.receipt.v1"}\n' >"$root/valid.json"
printf 'not-json\n' >"$root/invalid.json"
printf '{"outcome":"passed"} {"unexpected":true}\n' >"$root/trailing.json"

"$gxi" "$validator" "$root/valid.json"

set +e
"$gxi" "$validator" "$root/invalid.json" >/dev/null 2>&1
invalid_status=$?
"$gxi" "$validator" "$root/trailing.json" >/dev/null 2>&1
trailing_status=$?
set -e

[[ "$invalid_status" -ne 0 ]]
[[ "$trailing_status" -ne 0 ]]
