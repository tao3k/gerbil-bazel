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
schema=$(resolve_runfile "${3:?package receipt schema path is required}")
shift 3
if (($# == 0)); then
  echo "at least one package receipt path is required" >&2
  exit 1
fi
receipts=()
for receipt in "$@"; do
  receipts+=("$(resolve_runfile "$receipt")")
done

"$gxi" "$validator" "$schema" "${receipts[@]}"

valid_receipt='{"schema":"gerbil-bazel.package-receipt.v1","status":"ok","libraryOutputRequired":false,"packageIdentity":"test","packageReference":"test","packageRevision":"test"}'

invalid_receipts=(
  '{"schema":"gerbil-bazel.package-receipt.v1","status":"ok","libraryOutputRequired":false,"packageIdentity":"test","packageReference":"test"}'
  '{"schema":"gerbil-bazel.package-receipt.v1","status":"ok","libraryOutputRequired":false,"packageIdentity":"","packageReference":"test","packageRevision":"test"}'
  '{"schema":"gerbil-bazel.package-receipt.v1","status":"ok","libraryOutputRequired":false,"packageIdentity":"test","packageReference":"","packageRevision":"test"}'
  '{"schema":"gerbil-bazel.package-receipt.v1","status":"ok","libraryOutputRequired":false,"packageIdentity":"test","packageReference":"test","packageRevision":"test","durationSeconds":0}'
  '{"schema":"gerbil-bazel.package-receipt.v1","status":"ok","libraryOutputRequired":false,"packageIdentity":"test","packageReference":"test","packageRevision":"test","resourceBudget":{}}'
  '{"schema":"gerbil-bazel.package-receipt.v1","status":"ok","libraryOutputRequired":false,"packageIdentity":"test","packageReference":"test","packageRevision":"test","resourceGuard":{}}'
  '{"schema":"gerbil-bazel.package-receipt.v1","status":"ok","libraryOutputRequired":false,"packageIdentity":"test","packageReference":"test","packageRevision":"test","unknown":true}'
)

index=0
for payload in "${invalid_receipts[@]}"; do
  receipt="${TEST_TMPDIR:?TEST_TMPDIR is required}/invalid-package-receipt-$index.json"
  printf '%s\n' "$payload" >"$receipt"
  set +e
  "$gxi" "$validator" "$schema" "$receipt" >/dev/null 2>&1
  status=$?
  set -e
  if [[ $status -eq 0 ]]; then
    printf 'expected invalid package receipt to fail: %s\n' "$receipt" >&2
    exit 1
  fi
  index=$((index + 1))
done

valid_path="$TEST_TMPDIR/valid-package-receipt.json"
printf '%s\n' "$valid_receipt" >"$valid_path"
"$gxi" "$validator" "$schema" "$valid_path"
