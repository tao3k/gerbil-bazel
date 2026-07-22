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
fake_gxpkg="$temporary_root/fake-gxpkg"
rendered="$temporary_root/install-dependencies"
log="$temporary_root/gxpkg.log"
mkdir -p "$workspace"

cat >"$fake_gxpkg" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
{
  printf 'cwd=%s\n' "$PWD"
  printf 'gerbil-path=%s\n' "${GERBIL_PATH:-}"
  printf 'cc=%s\n' "${CC:-}"
  printf 'cpu-count=%s\n' "${GERBIL_BAZEL_CPU_COUNT:-}"
  printf 'build-cores=%s\n' "${GERBIL_BUILD_CORES:-}"
  printf 'argv='
  printf '<%s>' "$@"
  printf '\n'
} >>"${FAKE_GXPKG_LOG:?}"
EOF
chmod +x "$fake_gxpkg"

sed \
  -e "s|{{GXPKG}}|'$fake_gxpkg'|g" \
  -e "s|{{NATIVE_ENVIRONMENT_ARGS}}|'CC=fake-cc' 'GERBIL_BAZEL_CPU_COUNT=7'|g" \
  "$template" >"$rendered"
chmod +x "$rendered"

env -u GERBIL_PATH \
  BUILD_WORKSPACE_DIRECTORY="$workspace" \
  FAKE_GXPKG_LOG="$log" \
  "$rendered"

test -d "$workspace/.gerbil/pkg"
test "$(grep -c '^cwd=' "$log")" -eq 1
grep -F "cwd=$workspace" "$log" >/dev/null
grep -F "gerbil-path=$workspace/.gerbil" "$log" >/dev/null
grep -F 'cc=fake-cc' "$log" >/dev/null
grep -F 'cpu-count=7' "$log" >/dev/null
grep -F 'build-cores=1' "$log" >/dev/null
grep -F '<deps><--install>' "$log" >/dev/null
