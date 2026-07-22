#!/usr/bin/env bash
set -euo pipefail

workspace=${BUILD_WORKSPACE_DIRECTORY:?BUILD_WORKSPACE_DIRECTORY is required}
gerbil_root=${GERBIL_PATH:-"$workspace/.gerbil"}
gxpkg={{GXPKG}}
native_environment=({{NATIVE_ENVIRONMENT_ARGS}})
phase=initialize

report_failure() {
  local status=$?
  printf 'gerbil-bazel install_dependencies failed: phase=%s status=%s workspace=%s GERBIL_PATH=%s\n' \
    "$phase" "$status" "$workspace" "$gerbil_root" >&2
  exit "$status"
}
trap report_failure ERR

export GERBIL_PATH="$gerbil_root"
cd "$workspace"
mkdir -p "${gerbil_root%/}/pkg"

package_name_from_manifest() {
  local manifest=${1:?manifest path is required}
  tr '()\n\r\t' ' ' <"$manifest" |
    awk '{
      for (i = 1; i <= NF; i++) {
        if ($i == "package:" && i < NF) {
          print $(i + 1)
          exit
        }
      }
    }'
}

project_dependencies_ready() {
  local manifest="$workspace/gerbil.pkg"
  local dependency repository package package_manifest

  test -f "$manifest" || return 1
  mapfile -t dependencies < <(
    tr '()\n\r\t' ' ' <"$manifest" |
      awk '{
        inside = 0
        for (i = 1; i <= NF; i++) {
          if ($i == "depend:") {
            inside = 1
          } else if ($i == "policy:") {
            exit
          } else if (inside && $i ~ /^"/) {
            gsub(/^"/, "", $i)
            gsub(/"$/, "", $i)
            print $i
          }
        }
      }'
  )

  test "${#dependencies[@]}" -gt 0 || return 1
  for dependency in "${dependencies[@]}"; do
    repository=${dependency%@*}
    package=$repository
    package_manifest="${gerbil_root%/}/pkg/$repository/gerbil.pkg"
    if [[ -f "$package_manifest" ]]; then
      package=$(package_name_from_manifest "$package_manifest")
      test -n "$package" || package=$repository
    fi
    test -e "${gerbil_root%/}/lib/$package" || return 1
  done
}

phase=install
timeout_seconds=${GERBIL_BAZEL_INSTALL_TIMEOUT_SECONDS:-600}
/usr/bin/env "${native_environment[@]}" \
  "GERBIL_BUILD_CORES=${GERBIL_BAZEL_INSTALL_BUILD_CORES:-1}" \
  "$gxpkg" deps --install &
install_pid=$!
install_started_at=$SECONDS
while kill -0 "$install_pid" 2>/dev/null; do
  if (( timeout_seconds > 0 && SECONDS - install_started_at >= timeout_seconds )); then
    if project_dependencies_ready; then
      printf 'gerbil-bazel install_dependencies timed out after %ss; project dependencies are materialized, terminating gxpkg pid=%s\n' \
        "$timeout_seconds" "$install_pid" >&2
      kill "$install_pid" 2>/dev/null || true
      wait "$install_pid" 2>/dev/null || true
      exit 0
    fi
    printf 'gerbil-bazel install_dependencies timed out after %ss before project dependencies were ready; terminating gxpkg pid=%s\n' \
      "$timeout_seconds" "$install_pid" >&2
    kill "$install_pid" 2>/dev/null || true
    wait "$install_pid" 2>/dev/null || true
    exit 124
  fi
  sleep 1
done
wait "$install_pid"
