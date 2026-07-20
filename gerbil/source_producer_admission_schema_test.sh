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
schema=$(resolve_runfile "${3:?source producer admission schema path is required}")

"$gxi" "$validator" "$schema"
grep -F '"const": "gerbil-bazel.source-producer-admission.v1"' "$schema" >/dev/null
grep -F '"additionalProperties": false' "$schema" >/dev/null
grep -F '"allOf"' "$schema" >/dev/null
