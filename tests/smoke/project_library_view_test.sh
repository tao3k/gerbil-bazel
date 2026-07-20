#!/usr/bin/env bash
set -euo pipefail

receipt="${TEST_SRCDIR:?}/$1"

assert_receipt_field() {
  local field="$1"

  if ! grep -F "$field" "$receipt" >/dev/null; then
    echo "missing toolchain receipt field: $field" >&2
    sed -n '1,240p' "$receipt" >&2
    exit 1
  fi
}

if ! grep -Eq '"schema"[[:space:]]*:[[:space:]]*"gerbil-bazel\.(local|prebuilt)-toolchain-receipt\.v1"' "$receipt"; then
  echo "unsupported toolchain receipt schema" >&2
  sed -n '1,240p' "$receipt" >&2
  exit 1
fi

assert_receipt_field '"dependencyPolicy": "project-library-view"'
assert_receipt_field '"clan": "ready"'
assert_receipt_field '"gslph": "ready"'
