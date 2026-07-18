#!/usr/bin/env bash
set -euo pipefail

hash_stream() {
  if command -v shasum >/dev/null 2>&1; then
    shasum -a 1 | awk '{print $1}'
  elif command -v sha1sum >/dev/null 2>&1; then
    sha1sum | awk '{print $1}'
  else
    printf 'Gerbil Bazel requires shasum or sha1sum for ABI discovery\n' >&2
    exit 1
  fi
}

{
  uname -srm
  for tool in "$@"; do
    printf '%s\n' "$tool"
    if command -v shasum >/dev/null 2>&1; then
      shasum -a 1 "$tool"
    else
      sha1sum "$tool"
    fi
  done
} | hash_stream
