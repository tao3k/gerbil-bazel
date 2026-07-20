#!/usr/bin/env bash
set -euo pipefail

: "${GERBIL_INSTALL_CACHE_HIT:?GERBIL_INSTALL_CACHE_HIT is required}"
: "${GERBIL_INSTALL_DIGEST:?GERBIL_INSTALL_DIGEST is required}"
: "${GERBIL_PREFIX:?GERBIL_PREFIX is required}"

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
receipt_path="${GERBIL_INSTALL_MATERIALIZATION_RECEIPT:-$repo_root/.ci/receipts/gerbil-install-materialization.json}"
producer_receipt="$GERBIL_PREFIX/bootstrap.receipt.json"

if [[ ! "$GERBIL_INSTALL_DIGEST" =~ ^[0-9a-f]{64}$ ]]; then
  printf 'invalid Gerbil install digest: %s\n' "$GERBIL_INSTALL_DIGEST" >&2
  exit 64
fi
case "$GERBIL_INSTALL_CACHE_HIT" in
  true) materialization=cache-hit ;;
  false) materialization=built ;;
  *)
    printf 'GERBIL_INSTALL_CACHE_HIT must be true or false, got %s\n' \
      "$GERBIL_INSTALL_CACHE_HIT" >&2
    exit 64
    ;;
esac

if [[ ! -x "$GERBIL_PREFIX/bin/gxi" && ! -x "$GERBIL_PREFIX/current/bin/gxi" ]]; then
  printf 'Gerbil installation is missing executable gxi under %s\n' \
    "$GERBIL_PREFIX" >&2
  exit 65
fi
jq -e \
  --arg install_digest "$GERBIL_INSTALL_DIGEST" \
  '.schema == "gerbil-bazel.gerbil-bootstrap-receipt.v1" and
   .outcome == "ready" and
   .source_build_identity.installDigest == $install_digest' \
  "$producer_receipt" >/dev/null

if command -v sha256sum >/dev/null 2>&1; then
  producer_receipt_sha256="$(sha256sum "$producer_receipt" | awk '{print $1}')"
else
  producer_receipt_sha256="$(shasum -a 256 "$producer_receipt" | awk '{print $1}')"
fi

mkdir -p "$(dirname "$receipt_path")"
jq -n \
  --arg schema gerbil-bazel.install-materialization-receipt.v1 \
  --arg materialization "$materialization" \
  --arg install_digest "$GERBIL_INSTALL_DIGEST" \
  --arg prefix "$GERBIL_PREFIX" \
  --arg producer_receipt "$producer_receipt" \
  --arg producer_receipt_sha256 "$producer_receipt_sha256" \
  '{
    schema: $schema,
    outcome: "ready",
    materialization: $materialization,
    installDigest: $install_digest,
    prefix: $prefix,
    producerReceipt: {
      path: $producer_receipt,
      digestAlgorithm: "sha256",
      digest: $producer_receipt_sha256
    }
  }' >"$receipt_path"

jq -c . "$receipt_path"
