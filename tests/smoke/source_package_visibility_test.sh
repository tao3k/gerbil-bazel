#!/usr/bin/env bash
set -euo pipefail

resolve_runfile() {
  local key=${1:?runfile key is required}
  if [[ -n "${RUNFILES_DIR:-}" ]]; then
    printf '%s\n' "$RUNFILES_DIR/$key"
  elif [[ -n "${RUNFILES_MANIFEST_FILE:-}" ]]; then
    awk -v key="$key" '$1 == key {sub($1 " ", ""); print; exit}' "$RUNFILES_MANIFEST_FILE"
  else
    printf 'Bazel runfiles environment is unavailable\n' >&2
    return 1
  fi
}

package_file=$(resolve_runfile "${1:?package file runfile key is required}")
build_script=$(resolve_runfile "${2:?build script runfile key is required}")
receipt=$(resolve_runfile "${3:?source package receipt runfile key is required}")
nested_source=$(resolve_runfile "${4:?nested source runfile key is required}")

test -s "$package_file"
test -s "$build_script"
test -s "$receipt"
test -s "$nested_source"
grep -Eq '"package"[[:space:]]*:[[:space:]]*"gerbil-utils"' "$receipt"
grep -Eq '"sha256"[[:space:]]*:[[:space:]]*"e7777c505e71de490dc05f8e3ff4473dddbc998a99899c085d31750add551296"' "$receipt"
