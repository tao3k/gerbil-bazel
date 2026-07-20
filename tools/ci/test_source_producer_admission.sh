#!/usr/bin/env bash
set -euo pipefail

workspace="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
admission="$workspace/tools/ci/source_producer_admission.sh"
test_root="$(mktemp -d)"
trap 'rm -rf "$test_root"' EXIT

cache_hit_receipt="$test_root/cache-hit.json"
"$admission" true "" ubuntu-latest "$cache_hit_receipt" >/dev/null
jq -e '
  .schema == "gerbil-bazel.source-producer-admission.v1" and
  .outcome == "admitted" and
  .cacheHit == true and
  .runnerExplicit == false and
  .configuredRunner == null and
  .selectedRunner == "ubuntu-latest" and
  .sourceBuildRequired == false and
  .admitted == true and
  .reason == "complete-installation-cache-hit"
' "$cache_hit_receipt" >/dev/null

explicit_runner_receipt="$test_root/explicit-runner.json"
"$admission" false explicit-linux-x64-runner explicit-linux-x64-runner "$explicit_runner_receipt" >/dev/null
jq -e '
  .outcome == "admitted" and
  .cacheHit == false and
  .runnerExplicit == true and
  .configuredRunner == "explicit-linux-x64-runner" and
  .selectedRunner == "explicit-linux-x64-runner" and
  .sourceBuildRequired == true and
  .admitted == true and
  .reason == "explicit-runner-cold-build"
' "$explicit_runner_receipt" >/dev/null

blocked_receipt="$test_root/blocked.json"
if "$admission" "" "" ubuntu-latest "$blocked_receipt" >/dev/null 2>&1; then
  echo "implicit default runner unexpectedly admitted a cold build" >&2
  exit 1
fi
jq -e '
  .outcome == "blocked" and
  .cacheHit == false and
  .runnerExplicit == false and
  .configuredRunner == null and
  .selectedRunner == "ubuntu-latest" and
  .sourceBuildRequired == true and
  .admitted == false and
  .reason == "implicit-default-runner-cold-miss"
' "$blocked_receipt" >/dev/null

if "$admission" unknown "" ubuntu-latest "$test_root/invalid.json" >/dev/null 2>&1; then
  echo "invalid cache state unexpectedly admitted" >&2
  exit 1
fi

if "$admission" false runner-a runner-b "$test_root/mismatch.json" >/dev/null 2>&1; then
  echo "runner selection mismatch unexpectedly admitted" >&2
  exit 1
fi
