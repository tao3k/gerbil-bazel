#!/usr/bin/env bash
set -euo pipefail

if [[ "$#" -ne 2 ]]; then
  echo "usage: $0 <first-receipt> <replay-receipt>" >&2
  exit 2
fi

first_receipt="${TEST_SRCDIR:?}/$1"
replay_receipt="${TEST_SRCDIR:?}/$2"

grep -Eq '"schema"[[:space:]]*:[[:space:]]*"gerbil-bazel\.dependency-source-resolution-receipt\.v1"' "$first_receipt"
grep -Eq '"resolutionMode"[[:space:]]*:[[:space:]]*"identified-revision"' "$first_receipt"
grep -Eq '"canonicalPackagePath"[[:space:]]*:[[:space:]]*"\.gerbil/pkg/clan"' "$first_receipt"
grep -Eq '"expectedRevision"[[:space:]]*:[[:space:]]*"eaf43dc92bfeeb9abeb348137a7cca449843936f"' "$first_receipt"
grep -Eq '"observedRevision"[[:space:]]*:[[:space:]]*"eaf43dc92bfeeb9abeb348137a7cca449843936f"' "$first_receipt"
grep -Eq '"sourceSnapshotDigest"[[:space:]]*:[[:space:]]*"[0-9a-f]{40}"' "$first_receipt"
grep -Eq '"outcome"[[:space:]]*:[[:space:]]*"resolved"' "$first_receipt"

if ! cmp -s "${first_receipt}" "${replay_receipt}"; then
  echo "identified source replay receipts differ" >&2
  diff -u "${first_receipt}" "${replay_receipt}" >&2 || true
  exit 1
fi
