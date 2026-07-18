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
    grep -F '"DEVELOPER_DIR": '"\"$expected_developer_dir\"" "$receipt" >/dev/null
    grep -F '"SDKROOT": '"\"$expected_sdkroot\"" "$receipt" >/dev/null
    ;;
  Linux)
    if grep -F '"DEVELOPER_DIR"' "$receipt" >/dev/null || \
       grep -F '"SDKROOT"' "$receipt" >/dev/null; then
      printf 'Darwin SDK capability leaked into the Linux toolchain receipt\n' >&2
      exit 1
    fi
    ;;
  *)
    printf 'unsupported test host: %s\n' "$(uname -s)" >&2
    exit 1
    ;;
esac
