#!/usr/bin/env bash
set -euo pipefail

resolve_runfile() {
  local key=${1:?runfile key is required}
  if [[ -n "${RUNFILES_DIR:-}" ]]; then
    printf '%s\n' "$RUNFILES_DIR/$key"
  elif [[ -n "${RUNFILES_MANIFEST_FILE:-}" ]]; then
    awk -v key="$key" '$1 == key {sub($1 " ", ""); print; exit}' "$RUNFILES_MANIFEST_FILE"
  else
    printf 'Bazel runfiles environment is unavailable\n' >&2
    return 1
  fi
}

install_launcher=$(resolve_runfile "${1:?install launcher runfile key is required}")
template=$(resolve_runfile "${2:?install template runfile key is required}")
gxi=$(resolve_runfile "${3:?gxi runfile key is required}")
resource_policy=$(resolve_runfile "${4:?resource policy runfile key is required}")
functional=$(resolve_runfile "${5:?functional runfile key is required}")
test -x "$install_launcher"
test -x "$install_launcher.gxpkg"
test -f "$template"
test -x "$gxi"
test -f "$resource_policy"
test -f "$functional"

temporary_root=$(mktemp -d)
trap 'rm -rf "$temporary_root"' EXIT
workspace="$temporary_root/workspace"
fake_gxpkg="$temporary_root/fake-gxpkg"
rendered="$temporary_root/install-dependencies.ss"
log="$temporary_root/gxpkg.log"
mkdir -p "$workspace"
cp "$resource_policy" "$temporary_root/resource_policy.ss"
cp "$functional" "$temporary_root/functional.ss"

cat >"$fake_gxpkg" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
{
  printf 'cwd=%s\n' "$PWD"
  printf 'gerbil-path=%s\n' "${GERBIL_PATH:-}"
  printf 'cc=%s\n' "${CC:-}"
  printf 'build-cores=%s\n' "${GERBIL_BUILD_CORES:-}"
  printf 'argv='
  printf '<%s>' "$@"
  printf '\n'
} >>"${FAKE_GXPKG_LOG:?}"
if [[ "${FAKE_GXPKG_READY:-0}" == 1 ]]; then
  mkdir -p "${GERBIL_PATH:?}/lib/dependency-repo"
fi
if [[ -n "${FAKE_GXPKG_SLEEP_SECONDS:-}" ]]; then
  sleep "$FAKE_GXPKG_SLEEP_SECONDS"
fi
exit "${FAKE_GXPKG_STATUS:-0}"
EOF
chmod +x "$fake_gxpkg"

sed \
  -e "s|{{GXI_SHEBANG}}|$gxi|g" \
  -e "s|{{GXPKG_SCHEME}}|\"$fake_gxpkg\"|g" \
  -e 's|{{ENVIRONMENT_SETTERS}}|  (setenv "CC" "fake-cc") (setenv "GERBIL_BUILD_CORES" "6") (setenv "GERBIL_BAZEL_GUARD_LOGICAL_CPU_COUNT" "7") (setenv "GERBIL_BAZEL_GUARD_SYSTEM_MEMORY_BYTES" "21474836480") (setenv "GERBIL_BAZEL_GUARD_AVAILABLE_MEMORY_BYTES" "21474836480")|g' \
  "$template" >"$rendered"
chmod +x "$rendered"

cat >"$workspace/gerbil.pkg" <<'EOF'
(package: fixture
 depend: ("dependency-repo@revision")
 policy: ())
EOF

run_runner() {
  env -u GERBIL_PATH \
    BUILD_WORKSPACE_DIRECTORY="$workspace" \
    FAKE_GXPKG_LOG="$log" \
    "$@" \
    "$gxi" "$rendered"
}

run_runner
run_runner GERBIL_BAZEL_INSTALL_BUILD_CORES=3
run_runner GERBIL_BAZEL_INSTALL_MEMORY_PER_CORE_BYTES=4294967296
run_runner \
  GERBIL_BAZEL_INSTALL_BUILD_CORES=12 \
  GERBIL_BAZEL_INSTALL_MEMORY_PER_CORE_BYTES=4294967296

invalid_log="$temporary_root/invalid.log"
if run_runner GERBIL_BAZEL_INSTALL_BUILD_CORES=0 >"$invalid_log" 2>&1; then
  printf 'zero install build cores unexpectedly succeeded\n' >&2
  exit 1
fi
grep -F 'GERBIL_BAZEL_INSTALL_BUILD_CORES must be a positive integer' \
  "$invalid_log" >/dev/null

completed_child_log="$temporary_root/completed-child-71.log"
set +e
run_runner FAKE_GXPKG_STATUS=71 >"$completed_child_log" 2>&1
completed_child_status=$?
set -e
test "$completed_child_status" -eq 71
grep -F 'phase=install status=71' "$completed_child_log" >/dev/null

run_runner \
  FAKE_GXPKG_READY=1 \
  FAKE_GXPKG_SLEEP_SECONDS=3 \
  GERBIL_BAZEL_GUARD_TIMEOUT_SECONDS=1

rm -rf "$workspace/.gerbil/lib/dependency-repo"
not_ready_log="$temporary_root/not-ready.log"
set +e
run_runner \
  FAKE_GXPKG_SLEEP_SECONDS=3 \
  GERBIL_BAZEL_GUARD_TIMEOUT_SECONDS=1 \
  >"$not_ready_log" 2>&1
not_ready_status=$?
set -e
test "$not_ready_status" -eq 124
grep -F 'Scheme guard deadline before project dependencies were ready' \
  "$not_ready_log" >/dev/null

guard_receipt="$workspace/.gerbil/pkg/install-resource-guard.receipt.json"
test -f "$guard_receipt"
grep -F '"schema":"gerbil-bazel.resource-guard-receipt.v1"' \
  "$guard_receipt" >/dev/null
test -d "$workspace/.gerbil/pkg"
workspace_physical=$(cd "$workspace" && pwd -P)
grep -F "cwd=$workspace_physical" "$log" >/dev/null
grep -F "gerbil-path=$workspace/.gerbil" "$log" >/dev/null
grep -F 'cc=fake-cc' "$log" >/dev/null
grep -Fx 'build-cores=6' "$log" >/dev/null
grep -Fx 'build-cores=3' "$log" >/dev/null
grep -Fx 'build-cores=4' "$log" >/dev/null
grep -F '<deps><--install>' "$log" >/dev/null

compiled_workspace="$temporary_root/compiled-workspace"
compiled_log="$temporary_root/compiled-installer.log"
relocated_installer_directory="$temporary_root/relocated-installer"
relocated_install_launcher="$relocated_installer_directory/install_dependencies"
mkdir -p "$compiled_workspace"
mkdir -p "$relocated_installer_directory"
cp -p "$install_launcher" "$relocated_install_launcher"
cp -p "$install_launcher.gxpkg" "$relocated_install_launcher.gxpkg"
printf '(package: fixture)\n' >"$compiled_workspace/gerbil.pkg"
env -u GERBIL_PATH \
  BUILD_WORKSPACE_DIRECTORY="$compiled_workspace" \
  "$relocated_install_launcher" 2>"$compiled_log"

compiled_guard_receipt="$compiled_workspace/.gerbil/pkg/install-resource-guard.receipt.json"
test -f "$compiled_guard_receipt"
grep -F '"schema":"gerbil-bazel.resource-guard-receipt.v1"' \
  "$compiled_guard_receipt" >/dev/null
grep -F '"outcome":"completed"' "$compiled_guard_receipt" >/dev/null
grep -F '"exitCode":0' "$compiled_guard_receipt" >/dev/null
grep -F 'GERBIL_BAZEL_RESOURCE_BUDGET {"availableMemoryBytes":' \
  "$compiled_log" >/dev/null
grep -F '"schema":"gerbil-bazel.resource-budget.v1"' \
  "$compiled_log" >/dev/null
