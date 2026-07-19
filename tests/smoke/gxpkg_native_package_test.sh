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

gxpkg=$(resolve_runfile "${1:?gxpkg runfile key is required}")
gerbil_pkg=$(resolve_runfile "${2:?gerbil.pkg runfile key is required}")
build_script=$(resolve_runfile "${3:?build.ss runfile key is required}")
library_source=$(resolve_runfile "${4:?library source runfile key is required}")
main_source=$(resolve_runfile "${5:?main source runfile key is required}")

project=$(mktemp -d)
trap 'rm -rf "$project"' EXIT
mkdir -p "$project/native-math"
cp "$gerbil_pkg" "$project/gerbil.pkg"
cp "$build_script" "$project/build.ss"
cp "$library_source" "$project/native-math/lib.ss"
cp "$main_source" "$project/native-math/main.ss"

(
  cd "$project"
  GERBIL_PATH="$project/.gerbil" "$gxpkg" build
)

executable="$project/.gerbil/bin/native-math"
if [[ ! -x "$executable" ]]; then
  printf 'gxpkg native executable is unavailable: %s\n' "$executable" >&2
  exit 1
fi

output=$($executable)
if [[ "$output" != gxpkg-native-package-ok ]]; then
  printf 'unexpected gxpkg native executable output: %s\n' "$output" >&2
  exit 1
fi
