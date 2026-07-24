#!/usr/bin/env bash
set -euo pipefail

{{ENVIRONMENT}}
toolchain_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
runfiles_repository={{RUNFILES_REPOSITORY}}
runtime_toolchain_root=$toolchain_root
executable_runfiles_root=${0}.runfiles/$runfiles_repository
if [[ -d $executable_runfiles_root ]]; then
  runtime_toolchain_root=$executable_runfiles_root
elif [[ -n ${RUNFILES_DIR:-} && -d $RUNFILES_DIR/$runfiles_repository ]]; then
  runtime_toolchain_root=$RUNFILES_DIR/$runfiles_repository
fi
absolute_tool_path() {
  case "$1" in
    /*) printf '%s\n' "$1" ;;
    *) printf '%s/%s\n' "$PWD" "$1" ;;
  esac
}
export CC
CC=$(absolute_tool_path "$runtime_toolchain_root/gerbil-cc")
export GERBIL_GCC
GERBIL_GCC=$(absolute_tool_path "$runtime_toolchain_root/gerbil-gcc")
export GERBIL_GSC
GERBIL_GSC=$(absolute_tool_path "$runtime_toolchain_root/gerbil-gsc")
export GERBIL_NATIVE_ABI={{NATIVE_ABI}}

if (( $# == 0 )); then
  printf 'usage: native_scheme_env COMMAND [ARG ...]\n' >&2
  exit 64
fi

exec "$@"
