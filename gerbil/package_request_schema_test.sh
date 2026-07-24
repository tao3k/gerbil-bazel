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
schema=$(resolve_runfile "${3:?package request schema path is required}")

"$gxi" "$validator" "$schema"
grep -F '"const": "gerbil-bazel.package-request.v1"' "$schema" >/dev/null
grep -F '"additionalProperties": false' "$schema" >/dev/null
grep -F '"gxpkgManifest"' "$schema" >/dev/null
grep -F '"packageDependencies"' "$schema" >/dev/null
grep -F '"packageReference"' "$schema" >/dev/null
if grep -F '"receiptLinePrefix"' "$schema" >/dev/null; then
  echo "package request schema contains removed receiptLinePrefix" >&2
  exit 1
fi
