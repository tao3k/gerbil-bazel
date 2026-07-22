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
test -x "$install_launcher"
test -f "$template"

temporary_root=$(mktemp -d)
trap 'rm -rf "$temporary_root"' EXIT
workspace="$temporary_root/workspace"
fake_gxi="$temporary_root/fake-gxi"
fake_gxpkg="$temporary_root/fake-gxpkg"
fake_guard="$temporary_root/resource-guard.ss"
rendered="$temporary_root/install-dependencies"
gxi_log="$temporary_root/gxi.log"
log="$temporary_root/gxpkg.log"
mkdir -p "$workspace"

cat >"$fake_gxi" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
guard=${1:?resource guard path is required}
receipt=${2:?guard receipt path is required}
label=${3:?guard label is required}
timeout_seconds=${4:?guard timeout is required}
shift 4
{
  printf 'guard=%s\n' "$guard"
  printf 'receipt=%s\n' "$receipt"
  printf 'label=%s\n' "$label"
  printf 'timeout=%s\n' "$timeout_seconds"
  printf 'child='
  printf '<%s>' "$@"
  printf '\n'
} >>"${FAKE_GXI_LOG:?}"
mkdir -p "$(dirname "$receipt")"
status=${FAKE_GXI_STATUS:-0}
outcome=${FAKE_GXI_OUTCOME:-completed}
if [[ "${FAKE_GXI_WRITE_RECEIPT:-1}" == 1 ]]; then
  printf '{"schema":"gerbil-bazel.resource-guard-receipt.v1","outcome":"%s","exitCode":%d}\n' \
    "$outcome" "$status" >"$receipt"
fi
if [[ "$status" -ne 0 ]]; then
  if [[ "${FAKE_GXI_READY:-0}" == 1 ]]; then
    mkdir -p "${GERBIL_PATH:?}/lib/dependency-repo"
  fi
  exit "$status"
fi
exec "$@"
EOF
chmod +x "$fake_gxi"
printf 'fake Scheme resource guard\n' >"$fake_guard"

cat >"$fake_gxpkg" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
{
  printf 'cwd=%s\n' "$PWD"
  printf 'gerbil-path=%s\n' "${GERBIL_PATH:-}"
  printf 'cc=%s\n' "${CC:-}"
  printf 'cpu-count=%s\n' "${GERBIL_BAZEL_CPU_COUNT:-}"
  printf 'memory-bytes=%s\n' "${GERBIL_BAZEL_MEMORY_BYTES:-}"
  printf 'build-cores=%s\n' "${GERBIL_BUILD_CORES:-}"
  printf 'argv='
  printf '<%s>' "$@"
  printf '\n'
} >>"${FAKE_GXPKG_LOG:?}"
EOF
chmod +x "$fake_gxpkg"

sed \
  -e "s|{{GXI}}|'$fake_gxi'|g" \
  -e "s|{{GXPKG}}|'$fake_gxpkg'|g" \
  -e "s|{{NATIVE_ENVIRONMENT_ARGS}}|'CC=fake-cc' 'GERBIL_BUILD_CORES=6' 'GERBIL_BAZEL_CPU_COUNT=7' 'GERBIL_BAZEL_MEMORY_BYTES=17179869184'|g" \
  -e "s|{{RESOURCE_GUARD}}|'$fake_guard'|g" \
  "$template" >"$rendered"
chmod +x "$rendered"

cat >"$workspace/gerbil.pkg" <<'EOF'
(package: fixture
 depend: ("dependency-repo@revision")
 policy: ())
EOF

run_launcher() {
  env -u GERBIL_PATH \
    BUILD_WORKSPACE_DIRECTORY="$workspace" \
    FAKE_GXI_LOG="$gxi_log" \
    FAKE_GXPKG_LOG="$log" \
    "$@" \
    "$rendered"
}

run_launcher
run_launcher GERBIL_BAZEL_INSTALL_BUILD_CORES=3
run_launcher GERBIL_BAZEL_INSTALL_MEMORY_PER_CORE_BYTES=4294967296
run_launcher \
  GERBIL_BAZEL_INSTALL_BUILD_CORES=12 \
  GERBIL_BAZEL_INSTALL_MEMORY_PER_CORE_BYTES=4294967296

invalid_log="$temporary_root/invalid.log"
if run_launcher GERBIL_BAZEL_INSTALL_BUILD_CORES=0 >"$invalid_log" 2>&1; then
  printf 'zero install build cores unexpectedly succeeded\n' >&2
  exit 1
fi
grep -F 'GERBIL_BAZEL_INSTALL_BUILD_CORES must be a positive integer, got 0' \
  "$invalid_log" >/dev/null

run_launcher FAKE_GXI_STATUS=71 FAKE_GXI_OUTCOME=timeout FAKE_GXI_READY=1
completed_child_log="$temporary_root/completed-child-71.log"
set +e
run_launcher FAKE_GXI_STATUS=71 >"$completed_child_log" 2>&1
completed_child_status=$?
set -e
test "$completed_child_status" -eq 71
grep -F 'Scheme guard failed: status=71' "$completed_child_log" >/dev/null
guard_receipt="$workspace/.gerbil/pkg/install-resource-guard.receipt.json"
printf '{"schema":"gerbil-bazel.resource-guard-receipt.v1","outcome":"timeout","exitCode":71}\n' \
  >"$guard_receipt"
stale_receipt_log="$temporary_root/stale-receipt-71.log"
set +e
run_launcher FAKE_GXI_STATUS=71 FAKE_GXI_WRITE_RECEIPT=0 \
  >"$stale_receipt_log" 2>&1
stale_receipt_status=$?
set -e
test "$stale_receipt_status" -eq 71
test ! -e "$guard_receipt"
grep -F 'Scheme guard failed: status=71' "$stale_receipt_log" >/dev/null
rm -rf "$workspace/.gerbil/lib/dependency-repo"
not_ready_log="$temporary_root/not-ready.log"
set +e
run_launcher FAKE_GXI_STATUS=71 FAKE_GXI_OUTCOME=timeout \
  >"$not_ready_log" 2>&1
not_ready_status=$?
set -e
test "$not_ready_status" -eq 124
grep -F 'Scheme guard deadline before project dependencies were ready' \
  "$not_ready_log" >/dev/null

test -d "$workspace/.gerbil/pkg"
test "$(grep -c '^cwd=' "$log")" -eq 4
grep -F "cwd=$workspace" "$log" >/dev/null
grep -F "gerbil-path=$workspace/.gerbil" "$log" >/dev/null
grep -F 'cc=fake-cc' "$log" >/dev/null
grep -F 'cpu-count=7' "$log" >/dev/null
grep -F 'memory-bytes=17179869184' "$log" >/dev/null
test "$(grep -c '^build-cores=6$' "$log")" -eq 1
test "$(grep -c '^build-cores=3$' "$log")" -eq 1
test "$(grep -c '^build-cores=4$' "$log")" -eq 2
grep -F '<deps><--install>' "$log" >/dev/null
test "$(grep -c "^guard=$fake_guard$" "$gxi_log")" -eq 8
test "$(grep -c "^receipt=$workspace/.gerbil/pkg/install-resource-guard.receipt.json$" "$gxi_log")" -eq 8
test "$(grep -c '^label=install-dependencies$' "$gxi_log")" -eq 8
test "$(grep -c '^timeout=600$' "$gxi_log")" -eq 8
grep -F "child=<$fake_gxpkg><deps><--install>" "$gxi_log" >/dev/null
