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

phase=install
/usr/bin/env "${native_environment[@]}" \
  "$gxpkg" env env "${native_environment[@]}" "$gxpkg" deps --install
phase=list
/usr/bin/env "${native_environment[@]}" \
  "$gxpkg" env env "${native_environment[@]}" "$gxpkg" list
