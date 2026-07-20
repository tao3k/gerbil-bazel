#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
test_root="$(mktemp -d)"
trap 'rm -rf "$test_root"' EXIT

prefix="$test_root/prefix"
install_digest="$(printf 'a%.0s' {1..64})"
mkdir -p "$prefix/bin"
printf '%s\n' '#!/usr/bin/env bash' 'exit 0' >"$prefix/bin/gxi"
chmod +x "$prefix/bin/gxi"
jq -n \
  --arg install_digest "$install_digest" \
  '{
    schema: "gerbil-bazel.gerbil-bootstrap-receipt.v1",
    outcome: "ready",
    source_build_identity: {
      schema: "gerbil-bazel.source-build-identity.v1",
      installDigest: $install_digest
    }
  }' >"$prefix/bootstrap.receipt.json"

run_case() {
  local cache_hit=$1
  local expected=$2
  local receipt="$test_root/$expected.json"
  GERBIL_INSTALL_CACHE_HIT="$cache_hit" \
    GERBIL_INSTALL_DIGEST="$install_digest" \
    GERBIL_INSTALL_MATERIALIZATION_RECEIPT="$receipt" \
    GERBIL_PREFIX="$prefix" \
    "$repo_root/tools/ci/record_install_materialization.sh" >/dev/null
  jq -e \
    --arg expected "$expected" \
    --arg install_digest "$install_digest" \
    '.schema == "gerbil-bazel.install-materialization-receipt.v1" and
     .outcome == "ready" and
     .materialization == $expected and
     .installDigest == $install_digest and
     (.producerReceipt.digest | test("^[0-9a-f]{64}$"))' \
    "$receipt" >/dev/null
}

run_case true cache-hit
run_case false built

if GERBIL_INSTALL_CACHE_HIT=true \
  GERBIL_INSTALL_DIGEST="$(printf 'b%.0s' {1..64})" \
  GERBIL_INSTALL_MATERIALIZATION_RECEIPT="$test_root/mismatch.json" \
  GERBIL_PREFIX="$prefix" \
  "$repo_root/tools/ci/record_install_materialization.sh" >/dev/null 2>&1; then
  printf 'materialization receipt accepted a mismatched install digest\n' >&2
  exit 1
fi
