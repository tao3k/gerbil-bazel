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
runner=$(resolve_runfile "${2:?project runner path is required}")
root=${TEST_TMPDIR:?TEST_TMPDIR is required}/run-project
source_root=$root/source
tools_root=$root/tools
dependency_root=$root/dependency

mkdir -p "$source_root/src" "$tools_root" "$dependency_root"
printf 'build owner\n' >"$source_root/build.ss"
printf 'source owner\n' >"$source_root/src/module.ss"
printf 'dependency marker\n' >"$dependency_root/.marker"

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
  '[[ "${GERBIL_BUILD_CORES:-}" =~ ^[1-9][0-9]*$ ]]' \
  '[[ "$GERBIL_LOADPATH" == "$GERBIL_PATH/lib:"* ]]' \
  'project_root=$(cd "$(dirname "$build_script")" && pwd -P)' \
  '[[ "$PWD" == "$project_root" ]]' \
  'printf "%s\n" "$GERBIL_BUILD_CORES" >"$project_root/build-cores.txt"' \
  'if [[ "${FAKE_RECEIPT_MODE:-generic}" == link-failure ]]; then' \
  '  : "${GERBIL_BAZEL_FAILURE_RECEIPT_DIR:?}"' \
  '  printf '\''{"kind":"gerbil-bazel.compiler-failure-receipt.v1","version":1,"driver":"GERBIL_GSC","mode":"link","status":23}\n'\'' >"$GERBIL_BAZEL_FAILURE_RECEIPT_DIR/compiler-gsc-test.jsonl"' \
  '  for ((index = 0; index < 250; index++)); do printf "failure noise %03d\n" "$index"; done' \
  '  exit 23' \
  'fi' \
  'printf "generated\n" >"$project_root/src/generated.c"' \
  'if [[ "${FAKE_LIBRARY_OUTPUT:-0}" == 1 ]]; then' \
  '  mkdir -p "$GERBIL_PATH/lib/example"' \
  '  printf "compiled\n" >"$GERBIL_PATH/lib/example/module.o1"' \
  'fi' \
  'case "${FAKE_RECEIPT_MODE:-generic}" in' \
  '  valid) printf '\''PROJECT_RECEIPT {"outcome":"passed","schema":"test.project-receipt.v1"}\n'\'' ;;' \
  '  invalid) printf '\''PROJECT_RECEIPT not-json\n'\'' ;;' \
  '  *) printf '\''build completed\n'\'' ;;' \
  'esac' \
  >"$tools_root/gxi"
printf '%s\n' '#!/usr/bin/env bash' 'exit 0' >"$tools_root/tool"
chmod +x "$tools_root/gxi" "$tools_root/tool"

write_request() {
  local request=$1
  local output_root=$2
  local prefix=$3
  local build_destination=$4
  local source_destination=$5
  local name
  name=$(basename "$request" .request.json)
  printf '{"args":["compile"],"buildScript":"%s","dependencyRootMarker":"%s","log":"%s","packageIdentity":"","packageRevision":"","processGuard":false,"processGuardTimeoutSeconds":0,"projectDependencyRoots":[],"projectLabel":"//tests/smoke:fixture","projectRoot":"%s","receipt":"%s","receiptLinePrefix":"%s","requireLibraryOutput":false,"schema":"gerbil-bazel.project-request.v1","sources":[{"destination":"%s","source":"%s"},{"destination":"%s","source":"%s"}],"tools":{"as":"%s","cc":"%s","gxc":"%s","gxi":"%s","gxpkg":"%s","ld":"%s"}}\n' \
    "$build_destination" \
    "$dependency_root/.marker" \
    "$root/$name.log" \
    "$output_root" \
    "$root/$name.receipt.json" \
    "$prefix" \
    "$build_destination" \
    "$source_root/build.ss" \
    "$source_destination" \
    "$source_root/src/module.ss" \
    "$tools_root/tool" \
    "$tools_root/tool" \
    "$tools_root/tool" \
    "$tools_root/gxi" \
    "$tools_root/tool" \
    "$tools_root/tool" \
    >"$request"
}

run_fixture() {
  local name=$1
  local prefix=$2
  local output_root=$root/$name.project
  local request=$root/$name.request.json
  write_request \
    "$request" \
    "$output_root" \
    "$prefix" \
    external/package/build.ss \
    external/package/src/module.ss
  GERBIL_BAZEL_NATIVE_ABI=test-native-abi \
    GERBIL_BAZEL_GUARD_AVAILABLE_MEMORY_BYTES=68719476736 \
    GERBIL_BAZEL_GUARD_SYSTEM_MEMORY_BYTES=68719476736 \
    "$gxi" "$runner" "$request"
}

FAKE_RECEIPT_MODE=generic run_fixture generic ''
[[ ! -e "$root/generic.log.failure-receipts" ]]
grep -F '"schema":"gerbil-bazel.project-receipt.v1"' \
  "$root/generic.receipt.json" >/dev/null
grep -F '"libraryOutputRequired":false' \
  "$root/generic.receipt.json" >/dev/null
grep -F '"packageIdentity":""' "$root/generic.receipt.json" >/dev/null
grep -F '"packageRevision":""' "$root/generic.receipt.json" >/dev/null
grep -F '"resourceBudget":{' "$root/generic.receipt.json" >/dev/null
[[ -f "$root/generic.project/external/package/src/generated.c" ]]
[[ "$(<"$root/generic.project/external/package/build-cores.txt")" =~ ^[1-9][0-9]*$ ]]
[[ ! -e "$source_root/src/generated.c" ]]
[[ "$(<"$source_root/src/module.ss")" == 'source owner' ]]

GERBIL_BUILD_CORES=3 run_fixture explicit-build-cores ''
[[ "$(<"$root/explicit-build-cores.project/external/package/build-cores.txt")" == 3 ]]

set +e
GERBIL_BUILD_CORES=invalid run_fixture invalid-build-cores '' \
  2>"$root/invalid-build-cores.stderr"
invalid_build_cores_status=$?
set -e
[[ "$invalid_build_cores_status" -eq 66 ]]
grep -F 'GERBIL_BUILD_CORES must be a positive integer' \
  "$root/invalid-build-cores.stderr" >/dev/null

GERBIL_BAZEL_REQUIRE_LIBRARY_OUTPUT=1 FAKE_LIBRARY_OUTPUT=1 \
  run_fixture required-library ''
grep -F '"libraryOutputRequired":true' \
  "$root/required-library.receipt.json" >/dev/null
[[ -f "$root/required-library.project/.gerbil/lib/example/module.o1" ]]

set +e
GERBIL_BAZEL_REQUIRE_LIBRARY_OUTPUT=1 \
  run_fixture missing-library ''
missing_library_status=$?
set -e
[[ "$missing_library_status" -eq 66 ]]

set +e
FAKE_RECEIPT_MODE=link-failure \
  run_fixture link-failure '' 2>"$root/link-failure.stderr"
link_failure_status=$?
set -e
[[ "$link_failure_status" -eq 23 ]]
grep -F 'Gerbil project typed failure receipts follow' \
  "$root/link-failure.stderr" >/dev/null
grep -F '"kind":"gerbil-bazel.compiler-failure-receipt.v1"' \
  "$root/link-failure.stderr" >/dev/null
grep -F 'failure noise 249' "$root/link-failure.stderr" >/dev/null

FAKE_RECEIPT_MODE=valid run_fixture prefixed 'PROJECT_RECEIPT '
grep -F '"schema":"gerbil-bazel.project-receipt.v1"' \
  "$root/prefixed.receipt.json" >/dev/null
grep -F '"schema":"test.project-receipt.v1"' \
  "$root/prefixed.receipt.json" >/dev/null
grep -F 'PROJECT_RECEIPT ' "$root/prefixed.log" >/dev/null

set +e
FAKE_RECEIPT_MODE=invalid run_fixture invalid 'PROJECT_RECEIPT '
invalid_status=$?
set -e
[[ "$invalid_status" -eq 66 ]]

set +e
FAKE_RECEIPT_MODE=missing run_fixture missing 'PROJECT_RECEIPT '
missing_status=$?
set -e
[[ "$missing_status" -eq 66 ]]

unsafe_request=$root/unsafe.request.json
write_request \
  "$unsafe_request" \
  "$root/unsafe.project" \
  '' \
  build.ss \
  ../escape.ss
set +e
GERBIL_BAZEL_NATIVE_ABI=test-native-abi \
  "$gxi" "$runner" "$unsafe_request"
unsafe_status=$?
set -e
[[ "$unsafe_status" -eq 66 ]]
[[ ! -e "$root/escape.ss" ]]

duplicate_request=$root/duplicate.request.json
write_request \
  "$duplicate_request" \
  "$root/duplicate.project" \
  '' \
  build.ss \
  build.ss
mkdir -p "$root/duplicate.project"
printf 'preflight-sentinel\n' >"$root/duplicate.project/sentinel"
set +e
GERBIL_BAZEL_NATIVE_ABI=test-native-abi \
  "$gxi" "$runner" "$duplicate_request"
duplicate_status=$?
set -e
[[ "$duplicate_status" -eq 66 ]]
[[ "$(cat "$root/duplicate.project/sentinel")" == preflight-sentinel ]]

ancestor_target="$root/ancestor-symlink-target"
ancestor_link="$root/ancestor-symlink-parent"
ancestor_request="$root/ancestor-symlink.request.json"
ancestor_stderr="$root/ancestor-symlink.stderr"
mkdir -p "$ancestor_target"
printf 'ancestor-sentinel\n' >"$ancestor_target/sentinel"
ln -s "$ancestor_target" "$ancestor_link"
write_request \
  "$ancestor_request" \
  "$ancestor_link/project" \
  '' \
  external/package/build.ss \
  external/package/src/module.ss
set +e
GERBIL_BAZEL_NATIVE_ABI=test-native-abi \
  "$gxi" "$runner" "$ancestor_request" 2>"$ancestor_stderr"
ancestor_status=$?
set -e
[[ "$ancestor_status" -eq 66 ]]
grep -F 'Gerbil project root crosses a symlink below its authorized output envelope' \
  "$ancestor_stderr" >/dev/null
[[ "$(cat "$ancestor_target/sentinel")" == ancestor-sentinel ]]
[[ ! -e "$ancestor_target/project" ]]
[[ -L "$ancestor_link" ]]
