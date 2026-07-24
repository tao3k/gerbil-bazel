#!/usr/bin/env bash
set -euo pipefail

bazel_bin=${BAZEL:-bazelisk}
test_root=$(mktemp -d)
cleanup() {
  rm -rf "$test_root"
}
trap cleanup EXIT

action_graph="$test_root/package-action.textproto"
"$bazel_bin" aquery \
  'mnemonic("GerbilPackageBuild", @root_package//:package_0)' \
  --include_artifacts=true \
  --output=textproto \
  >"$action_graph"

if ! grep -F 'mnemonic: "GerbilPackageBuild"' "$action_graph" >/dev/null; then
  printf 'GerbilPackageBuild action is absent from the action graph\n' >&2
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

required_names=(
  package-runner
  functional-library
  resource-policy
)
required_patterns=(
  '(^|.*/)package_runner\.ss$'
  '(^|.*/)functional\.ss$'
  '(^|.*/)resource_policy\.ss$'
)
for index in "${!required_names[@]}"; do
  name=${required_names[$index]}
  pattern=${required_patterns[$index]}
  required_graph="$test_root/$name.textproto"
  query=$(printf \
    'inputs("%s", mnemonic("GerbilPackageBuild", @root_package//:package_0))' \
    "$pattern")
  "$bazel_bin" aquery "$query" --output=textproto >"$required_graph"
  if ! grep -F 'mnemonic: "GerbilPackageBuild"' "$required_graph" >/dev/null; then
    printf 'required Scheme package input is absent: %s\n' "$name" >&2
    exit 1
  fi
done

unrelated_names=(
  gxtest-executable
  native-scheme-environment
  toolchain-receipt
  dependency-installer
)
unrelated_patterns=(
  '(^|.*/)gxtest(\.sh|_raw)?$'
  '(^|.*/)native_scheme_env(\.sh)?$'
  '(^|.*/)toolchain\.receipt\.json$'
  '(^|.*/)install_gerbil_dependencies\.sh(\.tpl)?$'
)
for index in "${!unrelated_names[@]}"; do
  name=${unrelated_names[$index]}
  pattern=${unrelated_patterns[$index]}
  unrelated_graph="$test_root/$name.textproto"
  query=$(printf \
    'inputs("%s", mnemonic("GerbilPackageBuild", @root_package//:package_0))' \
    "$pattern")
  "$bazel_bin" aquery "$query" --output=textproto >"$unrelated_graph"
  if grep -F 'mnemonic: "GerbilPackageBuild"' "$unrelated_graph" >/dev/null; then
    printf 'unrelated toolchain input leaked into compile action: %s\n' \
      "$name" >&2
    exit 1
  fi
done

action_key=$(
  awk -F'"' '/action_key:/ {print $2; exit}' "$action_graph"
)
if [[ ! $action_key =~ ^[0-9a-f]{64}$ ]]; then
  printf 'package action key is missing or malformed: %s\n' "$action_key" >&2
  exit 1
fi

printf '{"actionKey":"%s","schema":"gerbil-bazel.package-action-boundary.v1","status":"passed"}\n' \
  "$action_key"
