#!/usr/bin/env bash
set -euo pipefail

: "${GERBIL_INSTALL_CACHE_HIT:?GERBIL_INSTALL_CACHE_HIT is required}"
: "${GERBIL_INSTALL_DIGEST:?GERBIL_INSTALL_DIGEST is required}"
: "${GERBIL_PREFIX:?GERBIL_PREFIX is required}"
: "${GERBIL_RUNNER_NAME:?GERBIL_RUNNER_NAME is required}"

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
receipt_path="${GERBIL_INSTALL_MATERIALIZATION_RECEIPT:-$repo_root/.ci/receipts/gerbil-install-materialization.json}"
producer_receipt="$GERBIL_PREFIX/bootstrap.receipt.json"

if [[ ! "$GERBIL_RUNNER_NAME" =~ [^[:space:]] ]]; then
  printf 'GERBIL_RUNNER_NAME must contain a non-whitespace character\n' >&2
  exit 64
fi

runner_system_raw="$(uname -s)"
case "$runner_system_raw" in
  Darwin)
    runner_system=darwin
    available_logical_cpu_count="$(sysctl -n hw.logicalcpu)"
    ;;
  Linux)
    runner_system=linux
    available_logical_cpu_count="$(getconf _NPROCESSORS_ONLN)"
    ;;
  *)
    printf 'unsupported runner system: %s\n' "$runner_system_raw" >&2
    exit 69
    ;;
esac

runner_architecture_raw="$(uname -m)"
case "$runner_architecture_raw" in
  x86_64 | amd64) runner_architecture=x86_64 ;;
  arm64 | aarch64) runner_architecture=aarch64 ;;
  *)
    printf 'unsupported runner architecture: %s\n' \
      "$runner_architecture_raw" >&2
    exit 69
    ;;
esac

if [[ ! "$available_logical_cpu_count" =~ ^[1-9][0-9]*$ ]]; then
  printf 'invalid available logical CPU count: %s\n' \
    "$available_logical_cpu_count" >&2
  exit 65
fi

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
  --arg runner_name "$GERBIL_RUNNER_NAME" \
  --arg runner_system "$runner_system" \
  --arg runner_architecture "$runner_architecture" \
  --argjson available_logical_cpu_count "$available_logical_cpu_count" \
  --arg producer_receipt "$producer_receipt" \
  --arg producer_receipt_sha256 "$producer_receipt_sha256" \
  '{
    schema: $schema,
    outcome: "ready",
    materialization: $materialization,
    installDigest: $install_digest,
    prefix: $prefix,
    runner: {
      name: $runner_name,
      system: $runner_system,
      architecture: $runner_architecture,
      availableLogicalCpuCount: $available_logical_cpu_count
    },
    producerReceipt: {
      path: $producer_receipt,
      digestAlgorithm: "sha256",
      digest: $producer_receipt_sha256
    }
  }' >"$receipt_path"

jq -c . "$receipt_path"
