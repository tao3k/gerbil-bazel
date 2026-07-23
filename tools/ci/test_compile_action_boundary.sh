#!/usr/bin/env bash
set -euo pipefail

bazel_bin=${BAZEL:-bazelisk}
test_root=$(mktemp -d)
cleanup() {
  rm -rf "$test_root"
}
trap cleanup EXIT

action_graph="$test_root/compile-action.textproto"
"$bazel_bin" aquery \
  'mnemonic("GerbilProjectCompile", //tests/smoke:compile)' \
  --include_artifacts=true \
  --output=textproto \
  >"$action_graph"

if ! grep -F 'mnemonic: "GerbilProjectCompile"' "$action_graph" >/dev/null; then
  printf 'GerbilProjectCompile action is absent from the action graph\n' >&2
  exit 1
fi

for scheduling_key in \
  GERBIL_BAZEL_CPU_COUNT \
  GERBIL_BAZEL_MEMORY_BYTES \
  GERBIL_BUILD_CORES
do
  if grep -F "key: \"$scheduling_key\"" "$action_graph" >/dev/null; then
    printf 'host scheduling key leaked into compile action identity: %s\n' \
      "$scheduling_key" >&2
    exit 1
  fi
done

for unrelated_runfile in \
  toolchain.receipt.json \
  native_scheme_env \
  gxtest
do
  if grep -F "$unrelated_runfile" "$action_graph" >/dev/null; then
    printf 'unrelated toolchain runfile leaked into compile action: %s\n' \
      "$unrelated_runfile" >&2
    exit 1
  fi
done

action_key=$(
  awk -F'"' '/action_key:/ {print $2; exit}' "$action_graph"
)
if [[ ! $action_key =~ ^[0-9a-f]{64}$ ]]; then
  printf 'compile action key is missing or malformed: %s\n' "$action_key" >&2
  exit 1
fi

printf '{"actionKey":"%s","schema":"gerbil-bazel.compile-action-boundary.v1","status":"passed"}\n' \
  "$action_key"
