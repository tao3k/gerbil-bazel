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
runner=$(resolve_runfile "${2:?package runner path is required}")
root=${TEST_TMPDIR:?TEST_TMPDIR is required}/run-package
source_root=$root/source
tools_root=$root/tools
dependency_root=$root/dependency

mkdir -p "$source_root/src" "$tools_root" "$dependency_root"
printf 'build owner\n' >"$source_root/build.ss"
printf '(package: example.invalid/runner)\n' >"$source_root/gerbil.pkg"
printf 'source owner\n' >"$source_root/src/module.ss"
printf 'dependency marker\n' >"$dependency_root/.marker"

printf '%s\n' \
  '#!/usr/bin/env bash' \
  'set -euo pipefail' \
  '[[ "${1:-}" == build ]]' \
  '[[ "${2:-}" == compile ]]' \
  'command -v gxc >/dev/null' \
  'command -v gxpkg >/dev/null' \
  'command -v cc >/dev/null' \
  'command -v as >/dev/null' \
  'command -v ld >/dev/null' \
  '[[ -n "${GERBIL_BAZEL_NATIVE_ABI:-}" ]]' \
  '[[ "${GERBIL_BUILD_CORES:-}" =~ ^[1-9][0-9]*$ ]]' \
  '[[ "$GERBIL_LOADPATH" == "$GERBIL_PATH/lib:"* ]]' \
  'package_root=$(pwd -P)' \
  'printf "%s\n" "$GERBIL_BUILD_CORES" >"$package_root/build-cores.txt"' \
  'if [[ "${FAKE_RECEIPT_MODE:-generic}" == link-failure ]]; then' \
  '  : "${GERBIL_BAZEL_FAILURE_RECEIPT_DIR:?}"' \
  '  printf '\''{"kind":"gerbil-bazel.compiler-failure-receipt.v1","version":1,"driver":"GERBIL_GSC","mode":"link","status":23}\n'\'' >"$GERBIL_BAZEL_FAILURE_RECEIPT_DIR/compiler-gsc-test.jsonl"' \
  '  for ((index = 0; index < 250; index++)); do printf "failure noise %03d\n" "$index"; done' \
  '  exit 23' \
  'fi' \
  'if [[ -n "${FAKE_DEPENDENCY_REFERENCE:-}" ]]; then' \
  '  [[ -f "$GERBIL_PATH/pkg/$FAKE_DEPENDENCY_REFERENCE.manifest" ]]' \
  'fi' \
  'printf "generated\n" >"$package_root/src/generated.c"' \
  'if [[ "${FAKE_LIBRARY_OUTPUT:-0}" == 1 ]]; then' \
  '  mkdir -p "$GERBIL_PATH/lib/example"' \
  '  printf "compiled\n" >"$GERBIL_PATH/lib/example/module.o1"' \
  'fi' \
  'printf '\''(def version-manifest (quote (("local-package" . "unknown") ("Gerbil" . "test-gerbil") ("Gambit" . "test-gambit"))))\n'\'' >"$package_root/manifest.ss"' \
  'printf '\''build completed\n'\''' \
  >"$tools_root/gxpkg"
printf '%s\n' '#!/usr/bin/env bash' 'exit 0' >"$tools_root/tool"
chmod +x "$tools_root/gxpkg" "$tools_root/tool"

write_request() {
  local request=$1
  local output_root=$2
  local manifest_destination=$3
  local source_destination=$4
  local name
  name=$(basename "$request" .request.json)
  local build_destination=${manifest_destination%gerbil.pkg}build.ss
  printf '{"args":["compile"],"dependencyRootMarker":"%s","gxpkgManifest":"%s","log":"%s","manifest":"%s","packageDependencies":%s,"packageDependencyRoots":[],"packageIdentity":"example.invalid/runner","packageLabel":"//tests/smoke:fixture","packageReference":"example.invalid/runner","packageRevision":"","packageRoot":"%s","processGuard":false,"processGuardTimeoutSeconds":0,"receipt":"%s","requireLibraryOutput":false,"schema":"gerbil-bazel.package-request.v1","sources":[{"destination":"%s","source":"%s"},{"destination":"%s","source":"%s"},{"destination":"%s","source":"%s"}],"tools":{"as":"%s","cc":"%s","gxc":"%s","gxi":"%s","gxpkg":"%s","ld":"%s"}}\n' \
    "$dependency_root/.marker" \
    "$root/$name.gxpkg-manifest" \
    "$root/$name.log" \
    "$manifest_destination" \
    "${REQUEST_DEPENDENCIES:-[]}" \
    "$output_root" \
    "$root/$name.receipt.json" \
    "$manifest_destination" \
    "$source_root/gerbil.pkg" \
    "$build_destination" \
    "$source_root/build.ss" \
    "$source_destination" \
    "$source_root/src/module.ss" \
    "$tools_root/tool" \
    "$tools_root/tool" \
    "$tools_root/tool" \
    "$tools_root/tool" \
    "$tools_root/gxpkg" \
    "$tools_root/tool" \
    >"$request"
}

run_fixture() {
  local name=$1
  local output_root=$root/$name.package
  local request=$root/$name.request.json
  write_request \
    "$request" \
    "$output_root" \
    external/package/gerbil.pkg \
    external/package/src/module.ss
  GERBIL_BAZEL_NATIVE_ABI=test-native-abi \
    GERBIL_BAZEL_GUARD_AVAILABLE_MEMORY_BYTES=68719476736 \
    GERBIL_BAZEL_GUARD_SYSTEM_MEMORY_BYTES=68719476736 \
    "$gxi" "$runner" "$request"
}

FAKE_RECEIPT_MODE=generic run_fixture generic
[[ ! -e "$root/generic.log.failure-receipts" ]]
grep -F '"schema":"gerbil-bazel.package-receipt.v1"' \
  "$root/generic.receipt.json" >/dev/null
grep -F '"libraryOutputRequired":false' \
  "$root/generic.receipt.json" >/dev/null
grep -F '"packageIdentity":"example.invalid/runner"' "$root/generic.receipt.json" >/dev/null
grep -F '"packageReference":"example.invalid/runner"' "$root/generic.receipt.json" >/dev/null
grep -F '"packageRevision":""' "$root/generic.receipt.json" >/dev/null
grep -F '"resourceBudget":{' "$root/generic.receipt.json" >/dev/null
grep -F '("example.invalid/runner" . "unknown")' "$root/generic.gxpkg-manifest" >/dev/null
[[ ! -e "$root/generic.package/.gerbil/pkg" ]]
[[ -f "$root/generic.package/external/package/src/generated.c" ]]
[[ "$(<"$root/generic.package/external/package/build-cores.txt")" =~ ^[1-9][0-9]*$ ]]
[[ ! -e "$source_root/src/generated.c" ]]
[[ "$(<"$source_root/src/module.ss")" == 'source owner' ]]

GERBIL_BUILD_CORES=3 run_fixture explicit-build-cores
[[ "$(<"$root/explicit-build-cores.package/external/package/build-cores.txt")" == 3 ]]

set +e
GERBIL_BUILD_CORES=invalid run_fixture invalid-build-cores \
  2>"$root/invalid-build-cores.stderr"
invalid_build_cores_status=$?
set -e
[[ "$invalid_build_cores_status" -eq 66 ]]
grep -F 'GERBIL_BUILD_CORES must be a positive integer' \
  "$root/invalid-build-cores.stderr" >/dev/null

GERBIL_BAZEL_REQUIRE_LIBRARY_OUTPUT=1 FAKE_LIBRARY_OUTPUT=1 \
  run_fixture required-library
grep -F '"libraryOutputRequired":true' \
  "$root/required-library.receipt.json" >/dev/null
[[ -f "$root/required-library.package/.gerbil/lib/example/module.o1" ]]

set +e
GERBIL_BAZEL_REQUIRE_LIBRARY_OUTPUT=1 \
  run_fixture missing-library
missing_library_status=$?
set -e
[[ "$missing_library_status" -eq 66 ]]

set +e
FAKE_RECEIPT_MODE=link-failure \
  run_fixture link-failure 2>"$root/link-failure.stderr"
link_failure_status=$?
set -e
[[ "$link_failure_status" -eq 23 ]]
grep -F 'Gerbil package typed failure receipts follow' \
  "$root/link-failure.stderr" >/dev/null
grep -F '"kind":"gerbil-bazel.compiler-failure-receipt.v1"' \
  "$root/link-failure.stderr" >/dev/null
grep -F 'failure noise 249' "$root/link-failure.stderr" >/dev/null

dependency_manifest=$root/dependency.gxpkg-manifest
printf '%s\n' \
  '(("github.com/example/dependency" . "abc123") ("Gerbil" . "test-gerbil") ("Gambit" . "test-gambit"))' \
  >"$dependency_manifest"
REQUEST_DEPENDENCIES='[{"manifest":"'"$dependency_manifest"'","reference":"github.com/example/dependency"}]' \
  FAKE_DEPENDENCY_REFERENCE=github.com/example/dependency \
  run_fixture dependency-manifest

printf '%s\n' \
  '(("github.com/example/wrong" . "abc123"))' \
  >"$dependency_manifest"
set +e
REQUEST_DEPENDENCIES='[{"manifest":"'"$dependency_manifest"'","reference":"github.com/example/dependency"}]' \
  FAKE_DEPENDENCY_REFERENCE=github.com/example/dependency \
  run_fixture dependency-manifest-reference-mismatch \
  2>"$root/dependency-manifest-reference-mismatch.stderr"
dependency_manifest_reference_mismatch_status=$?
set -e
[[ "$dependency_manifest_reference_mismatch_status" -eq 66 ]]
grep -F 'dependency gxpkg manifest identity does not match its reference' \
  "$root/dependency-manifest-reference-mismatch.stderr" >/dev/null

printf '%s\n' \
  '(("github.com/example/dependency" . "abc123"))' \
  '(("github.com/example/extra" . "def456"))' \
  >"$dependency_manifest"
set +e
REQUEST_DEPENDENCIES='[{"manifest":"'"$dependency_manifest"'","reference":"github.com/example/dependency"}]' \
  FAKE_DEPENDENCY_REFERENCE=github.com/example/dependency \
  run_fixture dependency-manifest-trailing-datum \
  2>"$root/dependency-manifest-trailing-datum.stderr"
dependency_manifest_trailing_datum_status=$?
set -e
[[ "$dependency_manifest_trailing_datum_status" -eq 66 ]]
grep -F 'dependency gxpkg manifest must contain exactly one datum' \
  "$root/dependency-manifest-trailing-datum.stderr" >/dev/null

unsafe_request=$root/unsafe.request.json
write_request \
  "$unsafe_request" \
  "$root/unsafe.package" \
  gerbil.pkg \
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
  "$root/duplicate.package" \
  gerbil.pkg \
  gerbil.pkg
mkdir -p "$root/duplicate.package"
printf 'preflight-sentinel\n' >"$root/duplicate.package/sentinel"
set +e
GERBIL_BAZEL_NATIVE_ABI=test-native-abi \
  "$gxi" "$runner" "$duplicate_request"
duplicate_status=$?
set -e
[[ "$duplicate_status" -eq 66 ]]
[[ "$(cat "$root/duplicate.package/sentinel")" == preflight-sentinel ]]

ancestor_target="$root/ancestor-symlink-target"
ancestor_link="$root/ancestor-symlink-parent"
ancestor_request="$root/ancestor-symlink.request.json"
ancestor_stderr="$root/ancestor-symlink.stderr"
mkdir -p "$ancestor_target"
printf 'ancestor-sentinel\n' >"$ancestor_target/sentinel"
ln -s "$ancestor_target" "$ancestor_link"
write_request \
  "$ancestor_request" \
  "$ancestor_link/package" \
  external/package/gerbil.pkg \
  external/package/src/module.ss
set +e
GERBIL_BAZEL_NATIVE_ABI=test-native-abi \
  "$gxi" "$runner" "$ancestor_request" 2>"$ancestor_stderr"
ancestor_status=$?
set -e
[[ "$ancestor_status" -eq 66 ]]
grep -F 'Gerbil package root crosses a symlink below its authorized output envelope' \
  "$ancestor_stderr" >/dev/null
[[ "$(cat "$ancestor_target/sentinel")" == ancestor-sentinel ]]
[[ ! -e "$ancestor_target/package" ]]
[[ -L "$ancestor_link" ]]
