#!/usr/bin/env bash
set -euo pipefail

workspace=${BUILD_WORKSPACE_DIRECTORY:?BUILD_WORKSPACE_DIRECTORY is required}
gerbil_root=${GERBIL_PATH:-"$workspace/.gerbil"}
gxpkg={{GXPKG}}
native_environment=({{NATIVE_ENVIRONMENT_ARGS}})

export GERBIL_PATH="$gerbil_root"
cd "$workspace"
mkdir -p "${gerbil_root%/}/pkg"

"$gxpkg" env env "${native_environment[@]}" "$gxpkg" deps --install
"$gxpkg" env env "${native_environment[@]}" "$gxpkg" list
