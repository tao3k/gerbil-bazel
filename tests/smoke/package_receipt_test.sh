#!/usr/bin/env sh
set -eu

resolve_runfile() {
  path=$1
  case "$path" in
    /*) printf '%s\n' "$path" ;;
    *) printf '%s/%s\n' "${TEST_SRCDIR:?TEST_SRCDIR is required}" "$path" ;;
  esac
}

receipt=$(resolve_runfile "${1:?package receipt path is required}")
package_identity=${2:?package identity is required}
package_revision=${3:?package revision is required}
grep -F '"packageIdentity":"'"$package_identity"'"' "$receipt" >/dev/null
grep -F '"packageRevision":"'"$package_revision"'"' "$receipt" >/dev/null
grep -F '"schema":"gerbil-bazel.project-receipt.v1"' "$receipt" >/dev/null
grep -F '"status":"ok"' "$receipt" >/dev/null
grep -F '"admissionOutcome":"ready"' "$receipt" >/dev/null
grep -F '"schema":"gerbil-bazel.resource-guard-receipt.v1"' "$receipt" >/dev/null
