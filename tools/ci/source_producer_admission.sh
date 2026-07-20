#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "usage: $0 <cache-hit> <configured-runner> <selected-runner> <receipt-path>" >&2
  exit 64
}

[[ $# -eq 4 ]] || usage

cache_hit_raw="$1"
configured_runner="$2"
selected_runner="$3"
receipt_path="$4"

[[ -n "$selected_runner" ]] || usage
if [[ -n "$configured_runner" && "$configured_runner" != "$selected_runner" ]]; then
  echo "configured and selected source-producer runners differ" >&2
  exit 64
fi

case "$cache_hit_raw" in
  true)
    cache_hit=true
    source_build_required=false
    admitted=true
    outcome=admitted
    reason=complete-installation-cache-hit
    ;;
  false | "")
    cache_hit=false
    source_build_required=true
    if [[ -n "$configured_runner" ]]; then
      admitted=true
      outcome=admitted
      reason=explicit-runner-cold-build
    else
      admitted=false
      outcome=blocked
      reason=implicit-default-runner-cold-miss
    fi
    ;;
  *)
    echo "invalid actions/cache cache-hit value: $cache_hit_raw" >&2
    exit 64
    ;;
esac

if [[ -n "$configured_runner" ]]; then
  runner_explicit=true
else
  runner_explicit=false
fi

mkdir -p "$(dirname "$receipt_path")"
receipt_tmp="$(mktemp "${receipt_path}.tmp.XXXXXX")"
trap 'rm -f "$receipt_tmp"' EXIT

jq -n \
  --arg schema "gerbil-bazel.source-producer-admission.v1" \
  --arg outcome "$outcome" \
  --arg configuredRunner "$configured_runner" \
  --arg selectedRunner "$selected_runner" \
  --arg reason "$reason" \
  --argjson cacheHit "$cache_hit" \
  --argjson runnerExplicit "$runner_explicit" \
  --argjson sourceBuildRequired "$source_build_required" \
  --argjson admitted "$admitted" \
  '{
    schema: $schema,
    outcome: $outcome,
    cacheHit: $cacheHit,
    runnerExplicit: $runnerExplicit,
    configuredRunner: ($configuredRunner | if length == 0 then null else . end),
    selectedRunner: $selectedRunner,
    sourceBuildRequired: $sourceBuildRequired,
    admitted: $admitted,
    reason: $reason
  }' >"$receipt_tmp"

mv "$receipt_tmp" "$receipt_path"
trap - EXIT
jq -c . "$receipt_path"

if [[ "$admitted" != true ]]; then
  echo "cold source build requires an explicit GERBIL_SOURCE_RUNNER" >&2
  exit 1
fi
