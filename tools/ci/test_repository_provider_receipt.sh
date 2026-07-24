#!/usr/bin/env bash
set -euo pipefail

if [[ $# != 2 ]]; then
  printf 'usage: %s <provider> <receipt-path>\n' "$0" >&2
  exit 64
fi

repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
provider="$1"
receipt_path="$2"
rm -f -- "$receipt_path"
case "$receipt_path" in
  /*) ;;
  *) receipt_path="$repo_root/$receipt_path" ;;
esac

test_root="$(mktemp -d)"
cleanup() {
  rm -rf "$test_root"
}
trap cleanup EXIT

stdout_path="$test_root/stdout"
stdout_receipt_path="$test_root/stdout-receipt.json"

GERBIL_REPOSITORY_PROVIDER_TEST_RECEIPT="$receipt_path" \
  "$repo_root/tools/ci/test_repository_provider.sh" "$provider" \
  | tee "$stdout_path"

if [[ ! -s "$receipt_path" ]]; then
  printf 'repository-provider test did not persist receipt: %s\n' \
    "$receipt_path" >&2
  exit 1
fi

tail -n 1 "$stdout_path" >"$stdout_receipt_path"
jq -e \
  '.schema == "gerbil-bazel.repository-provider-test-receipt.v1"' \
  "$stdout_receipt_path" >/dev/null
jq -e \
  '.schema == "gerbil-bazel.repository-provider-test-receipt.v1"' \
  "$receipt_path" >/dev/null
cmp "$stdout_receipt_path" "$receipt_path"
