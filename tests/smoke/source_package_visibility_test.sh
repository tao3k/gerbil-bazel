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
resolution_receipt=$(resolve_runfile "${4:?source resolution receipt runfile key is required}")
nested_source=$(resolve_runfile "${5:?nested source runfile key is required}")

test -s "$package_file"
test -s "$build_script"
test -s "$receipt"
test -s "$resolution_receipt"
test -s "$nested_source"
grep -Eq '"package"[[:space:]]*:[[:space:]]*"gerbil-utils"' "$receipt"
grep -Eq '"sha256"[[:space:]]*:[[:space:]]*"e7777c505e71de490dc05f8e3ff4473dddbc998a99899c085d31750add551296"' "$receipt"
grep -Eq '"schema"[[:space:]]*:[[:space:]]*"gerbil-bazel\.dependency-source-resolution-receipt\.v1"' "$resolution_receipt"
grep -Eq '"resolutionMode"[[:space:]]*:[[:space:]]*"hermetic-archive"' "$resolution_receipt"
grep -Eq '"canonicalUri"[[:space:]]*:[[:space:]]*"https://github.com/mighty-gerbils/gerbil-utils"' "$resolution_receipt"
grep -Eq '"expectedRevision"[[:space:]]*:[[:space:]]*"f45a4ef3bfecd2af39e114ed736ce9082cbb8244"' "$resolution_receipt"
grep -Eq '"sourceSnapshotDigest"[[:space:]]*:[[:space:]]*"sha256:e7777c505e71de490dc05f8e3ff4473dddbc998a99899c085d31750add551296"' "$resolution_receipt"
grep -Eq '"outcome"[[:space:]]*:[[:space:]]*"resolved"' "$resolution_receipt"
