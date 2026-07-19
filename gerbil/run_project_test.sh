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

runner=$(resolve_runfile "${1:?run_project path is required}")
root=${TEST_TMPDIR:?TEST_TMPDIR is required}/run-project
source_root=$root/source
tools_root=$root/tools
dependency_root=$root/dependency
manifest=$root/sources

mkdir -p "$source_root/src" "$tools_root" "$dependency_root"
printf 'build owner\n' >"$source_root/build.ss"
printf 'source owner\n' >"$source_root/src/module.ss"
printf 'dependency marker\n' >"$dependency_root/.marker"
printf '%s\t%s\n' \
  "$source_root/build.ss" build.ss \
  "$source_root/src/module.ss" src/module.ss \
  >"$manifest"

printf '%s\n' \
  '#!/usr/bin/env bash' \
  'set -euo pipefail' \
  'build_script=${1:?}' \
  '[[ "${2:-}" == compile ]]' \
  'command -v gxc >/dev/null' \
  'command -v gxpkg >/dev/null' \
  'command -v cc >/dev/null' \
  'command -v as >/dev/null' \
  'command -v ld >/dev/null' \
  '[[ -n "${GERBIL_BAZEL_NATIVE_ABI:-}" ]]' \
  '[[ "$GERBIL_LOADPATH" == "$GERBIL_PATH/lib:"* ]]' \
  'project_root=$(cd "$(dirname "$build_script")" && pwd -P)' \
  'printf "generated\n" >"$project_root/src/generated.c"' \
  'case "${FAKE_RECEIPT_MODE:-generic}" in' \
  '  valid) printf '\''PROJECT_RECEIPT {"outcome":"passed","schema":"test.project-receipt.v1"}\n'\'' ;;' \
  '  *) printf '\''build completed\n'\'' ;;' \
  'esac' \
  >"$tools_root/gxi"
printf '%s\n' '#!/usr/bin/env bash' 'exit 0' >"$tools_root/tool"
chmod +x "$tools_root/gxi" "$tools_root/tool"

run_fixture() {
  local name=$1
  local prefix=$2
  local output_root=$root/$name.project
  GERBIL_BAZEL_NATIVE_ABI=test-native-abi \
    "$runner" \
      "$tools_root/gxi" \
      "$tools_root/tool" \
      "$tools_root/tool" \
      "$tools_root/tool" \
      "$tools_root/tool" \
      "$tools_root/tool" \
      "$dependency_root/.marker" \
      "$manifest" \
      "$output_root" \
      build.ss \
      "$root/$name.receipt.json" \
      "$root/$name.log" \
      "$prefix" \
      compile
}

FAKE_RECEIPT_MODE=generic run_fixture generic ''
grep -F '"schema":"gerbil-bazel.project-receipt.v1"' \
  "$root/generic.receipt.json" >/dev/null
[[ -f "$root/generic.project/src/generated.c" ]]
[[ ! -e "$source_root/src/generated.c" ]]
[[ "$(<"$source_root/src/module.ss")" == 'source owner' ]]

FAKE_RECEIPT_MODE=valid run_fixture prefixed 'PROJECT_RECEIPT '
grep -Fx '{"outcome":"passed","schema":"test.project-receipt.v1"}' \
  "$root/prefixed.receipt.json" >/dev/null
grep -F 'PROJECT_RECEIPT ' "$root/prefixed.log" >/dev/null

set +e
FAKE_RECEIPT_MODE=missing run_fixture missing 'PROJECT_RECEIPT '
missing_status=$?
set -e
[[ "$missing_status" -eq 65 ]]

printf '%s\t%s\n' "$source_root/build.ss" ../escape.ss >"$root/unsafe.sources"
set +e
GERBIL_BAZEL_NATIVE_ABI=test-native-abi \
  "$runner" \
    "$tools_root/gxi" "$tools_root/tool" "$tools_root/tool" \
    "$tools_root/tool" "$tools_root/tool" "$tools_root/tool" \
    "$dependency_root/.marker" "$root/unsafe.sources" \
    "$root/unsafe.project" build.ss "$root/unsafe.receipt.json" \
    "$root/unsafe.log" '' compile
unsafe_status=$?
set -e
[[ "$unsafe_status" -eq 64 ]]
[[ ! -e "$root/escape.ss" ]]
