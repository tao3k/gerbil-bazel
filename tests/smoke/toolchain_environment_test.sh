#!/usr/bin/env bash
set -euo pipefail

runfile_key=${1:?toolchain receipt runfile key is required}
if [[ -n "${RUNFILES_DIR:-}" ]]; then
  receipt="$RUNFILES_DIR/$runfile_key"
elif [[ -n "${RUNFILES_MANIFEST_FILE:-}" ]]; then
  receipt="$(awk -v key="$runfile_key" '$1 == key {sub($1 " ", ""); print; exit}' "$RUNFILES_MANIFEST_FILE")"
else
  printf 'Bazel runfiles environment is unavailable\n' >&2
  exit 1
fi

if [[ ! -f "$receipt" ]]; then
  printf 'toolchain receipt is unavailable: %s\n' "$receipt" >&2
  exit 1
fi

case "$(uname -s)" in
  Darwin)
    expected_developer_dir="$(/usr/bin/env -u DEVELOPER_DIR -u SDKROOT /usr/bin/xcode-select -p)"
    expected_sdkroot="$(/usr/bin/env -u DEVELOPER_DIR -u SDKROOT /usr/bin/xcrun --sdk macosx --show-sdk-path)"
    expected_executable_linker="$(/usr/bin/env -u DEVELOPER_DIR -u SDKROOT /usr/bin/xcrun --sdk macosx --find clang)"
    expected_cpu_count="$(/usr/sbin/sysctl -n hw.logicalcpu)"
    grep -F '"DEVELOPER_DIR": '"\"$expected_developer_dir\"" "$receipt" >/dev/null
    grep -F '"SDKROOT": '"\"$expected_sdkroot\"" "$receipt" >/dev/null
    grep -F '"gambitDynamicLinkOptions": "-Wl,-undefined,dynamic_lookup"' "$receipt" >/dev/null
    grep -F '"gerbilExecutableLinker": '"\"$expected_executable_linker\"" "$receipt" >/dev/null
    ;;
  Linux)
    expected_cpu_count="$(getconf _NPROCESSORS_ONLN)"
    if grep -F '"DEVELOPER_DIR"' "$receipt" >/dev/null || \
       grep -F '"SDKROOT"' "$receipt" >/dev/null; then
      printf 'Darwin SDK capability leaked into the Linux toolchain receipt\n' >&2
      exit 1
    fi
    grep -F '"gambitDynamicLinkOptions": ""' "$receipt" >/dev/null
    grep -F '"gerbilExecutableLinker": ""' "$receipt" >/dev/null
    ;;
  *)
    printf 'unsupported test host: %s\n' "$(uname -s)" >&2
    exit 1
    ;;
esac

build_cores="$(awk -F'"' '/"GERBIL_BUILD_CORES":/ {print $4; exit}' "$receipt")"
build_cores_receipt="$(awk -F': ' '/"gerbilBuildCores":/ {gsub(/[, ]/, "", $2); print $2; exit}' "$receipt")"
build_cores_source="$(awk -F'"' '/"gerbilBuildCoresSource":/ {print $4; exit}' "$receipt")"

if [[ ! "$build_cores" =~ ^[1-9][0-9]*$ ]]; then
  printf 'GERBIL_BUILD_CORES is not a positive integer: %s\n' "$build_cores" >&2
  exit 1
fi
if [[ "$build_cores_receipt" != "$build_cores" ]]; then
  printf 'Gerbil build-core receipt disagrees with the toolchain environment: %s != %s\n' \
    "$build_cores_receipt" "$build_cores" >&2
  exit 1
fi

case "$build_cores_source" in
  host-system)
    if [[ "$build_cores" != "$expected_cpu_count" ]]; then
      printf 'adaptive Gerbil worker count disagrees with host capacity: %s != %s\n' \
        "$build_cores" "$expected_cpu_count" >&2
      exit 1
    fi
    ;;
  process-environment | repository-environment)
    ;;
  *)
    printf 'unknown Gerbil build-core source: %s\n' "$build_cores_source" >&2
    exit 1
    ;;
esac
