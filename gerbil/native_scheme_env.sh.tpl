#!/usr/bin/env bash
set -euo pipefail

{{ENVIRONMENT}}
export GERBIL_NATIVE_ABI={{NATIVE_ABI}}

if (( $# == 0 )); then
  printf 'usage: native_scheme_env COMMAND [ARG ...]\n' >&2
  exit 64
fi

exec "$@"
